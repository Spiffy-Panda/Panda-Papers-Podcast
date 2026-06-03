using System.ComponentModel;
using ModelContextProtocol.Server;
using PaperCoach.Server.Models;
using PaperCoach.Server.Services;
using Tts;

namespace PaperCoach.Server.Mcp;

/// <summary>
/// The director's verb set. Every tool is a deterministic file-I/O
/// operation over the project's papers/ and input/ directories — LLM
/// judgement happens in the SKILL.md files that call these, not here.
/// Tool names are snake_case (MCP convention) regardless of the C# method.
/// </summary>
[McpServerToolType]
public sealed class PaperCoachTools(
    RepoRoot root,
    Workspace workspace,
    SessionStore sessions,
    Extractor extractor,
    PartPlanner planner,
    AudioRenderer renderer,
    Speaker speaker)
{
    [McpServerTool(Name = "list_papers")]
    [Description(
        "Enumerate every paper available in this project. Reads " +
        "papers/<slug>/paper.meta.json for new-pipeline papers and " +
        "input/<slug>_paper.json for legacy ones, returning a unified " +
        "listing with slug, title, authors, year, and flags for which " +
        "downstream artifacts (paper.md, graph.cypher, highlights.json) " +
        "already exist on disk. Cheap — call this freely to refresh the " +
        "director's view of what's available.")]
    public IReadOnlyList<PaperListing> ListPapers() => workspace.ListPapers();

    [McpServerTool(Name = "find_papers")]
    [Description(
        "Filter list_papers by simple substring/equality criteria. " +
        "Pass any combination of: author (substring match, any author), " +
        "year (exact int), title (substring), slug (substring). All " +
        "supplied criteria AND together. Concept-based search via " +
        "graph.cypher is not implemented yet — that lights up once " +
        "paper-to-cypher has produced graphs for the candidate papers.")]
    public IReadOnlyList<PaperListing> FindPapers(
        [Description("Substring to match against any author name. Case-insensitive.")]
        string? author = null,
        [Description("Exact publication year.")]
        int? year = null,
        [Description("Substring to match against the paper title. Case-insensitive.")]
        string? title = null,
        [Description("Substring to match against the paper slug. Case-insensitive.")]
        string? slug = null)
    {
        var all = workspace.ListPapers();
        return all.Where(p =>
                (author is null ||
                    p.Meta.Authors.Any(a =>
                        a.Contains(author, StringComparison.OrdinalIgnoreCase))) &&
                (year is null || p.Meta.Year == year) &&
                (title is null ||
                    p.Meta.Title.Contains(title, StringComparison.OrdinalIgnoreCase)) &&
                (slug is null ||
                    p.Slug.Contains(slug, StringComparison.OrdinalIgnoreCase)))
            .ToList();
    }

    [McpServerTool(Name = "inspect_paper")]
    [Description(
        "Return one paper's metadata, its section index (id, title, " +
        "paragraph count), and optionally the body text of named " +
        "sections. Pass sections=[\"abstract\",\"conclusion\"] to pull " +
        "those bodies; omit sections to get just the index. Returns null " +
        "if the slug is unknown — use list_papers to discover valid slugs.")]
    public PaperDetail? InspectPaper(
        [Description("Paper slug as returned by list_papers.")]
        string slug,
        [Description(
            "Optional section ids to include as full text in the response " +
            "(e.g. [\"abstract\",\"conclusion\"]). Section ids come from " +
            "the index returned in this same call's `sections` field.")]
        string[]? sections = null)
        => workspace.Inspect(slug, sections);

    [McpServerTool(Name = "start_session")]
    [Description(
        "Create a new workspace session under papers/_workspace/<id>/. " +
        "Returns the session id, which subsequent tools (select, extract, " +
        "combine, session_status) need as their first argument. One " +
        "session per chat-driven exploration is the convention — they're " +
        "cheap and isolate composed.md / script.json / etc. from each " +
        "other.")]
    public SessionRef StartSession(
        [Description("Optional human-readable label stored alongside the session id.")]
        string? name = null)
        => sessions.Start(name);

    [McpServerTool(Name = "list_sessions")]
    [Description(
        "List all workspace sessions, newest first by updated_utc. Use " +
        "this to find an existing session to resume rather than always " +
        "calling start_session. Each entry includes id, name, " +
        "created_utc, updated_utc, current selection, and registered " +
        "artifacts.")]
    public IReadOnlyList<SessionState> ListSessions() => sessions.List();

    [McpServerTool(Name = "plan_parts")]
    [Description(
        "Section-aware podcast part plan for a paper. Returns an ordered " +
        "list of parts, each with the paragraph_ids it should cover plus " +
        "the section_ids/section_titles those paragraphs came from. " +
        "Algorithm: accumulate whole sections into the current part until " +
        "adding the next would exceed max_per_part AND the current already " +
        "has min_per_part, then flush. Long sections get sliced; a short " +
        "trailing part merges into its predecessor. Pure — writes nothing. " +
        "The scripter decides whether to persist this as a parts plan or " +
        "iterate over it directly.")]
    public IReadOnlyList<PlannedPart> PlanParts(
        [Description("Paper slug as returned by list_papers.")]
        string slug,
        [Description("Minimum paragraphs per part. Default 3.")]
        int min_per_part = 3,
        [Description("Maximum paragraphs per part. Default 7. Must be ≥ min_per_part.")]
        int max_per_part = 7)
        => planner.Plan(slug, min_per_part, max_per_part);

    [McpServerTool(Name = "select")]
    [Description(
        "Set or update a session's working selection of papers. Pass " +
        "plain slugs ([\"a\",\"b\"]) to REPLACE the current selection. " +
        "Pass prefixed slugs ([\"+c\",\"-a\"]) to ADD/REMOVE relative to " +
        "the current selection. Mixing plain and prefixed slugs in one " +
        "call is rejected — too easy to mean the wrong thing.")]
    public SessionState Select(
        [Description("Session id returned by start_session.")]
        string session,
        [Description(
            "Slugs to assign to the session. Plain = replace; +slug/-slug = delta.")]
        string[] slugs)
        => sessions.Select(session, slugs);

    [McpServerTool(Name = "extract")]
    [Description(
        "Pull named sections from the given papers into a single composed " +
        "markdown file under the session dir. Writes three files: the .md " +
        "itself, a .spans.json mapping each (slug, section_id) to its " +
        "line range in the .md (for player sync), and a .md.sha256 for " +
        "freshness checks. Slugs not found, or sections missing from a " +
        "given paper, are returned in the `missing` field rather than " +
        "failing the whole call.")]
    public ExtractResult Extract(
        [Description("Session id returned by start_session.")]
        string session,
        [Description("Paper slugs to extract from.")]
        string[] slugs,
        [Description(
            "Section ids to pull from each paper (e.g. [\"abstract\",\"conclusion\"]). " +
            "Same set is applied to every slug.")]
        string[] sections,
        [Description(
            "Output filename relative to the session dir. Conventional: " +
            "\"composed.md\". Must not escape the session dir.")]
        string into = "composed.md")
        => extractor.Extract(session, slugs, sections, into);

    [McpServerTool(Name = "combine")]
    [Description(
        "Concatenate existing markdown files into a single composed file " +
        "under the session dir. Same side-outputs as extract: .spans.json " +
        "and .md.sha256. Use this to merge an extracted composed.md with " +
        "a separately-written intro/conclusion MD, for example.")]
    public ExtractResult Combine(
        [Description("Session id returned by start_session.")]
        string session,
        [Description(
            "Paths to existing markdown files, relative to the project root " +
            "(or absolute). Files not found are reported in `missing`.")]
        string[] files,
        [Description(
            "Output filename relative to the session dir. Must not escape " +
            "the session dir.")]
        string into)
        => extractor.Combine(session, files, into);

    [McpServerTool(Name = "render_audio")]
    [Description(
        "Render a podcast audioscript to WAV files via the shared C# TTS " +
        "library. Accepts two shapes (see PIPELINE-DECISIONS.md §5): " +
        "multi-part script.json (`{paper_slug, speaker_a, speaker_b, " +
        "parts: [{part_of, lines, ...}]}`), or a single legacy " +
        "part_NN.json (`{lines, pause_between_ms, rate, ...}`). Detection " +
        "is by presence of a top-level `parts` array. Output: stable-named " +
        "part_NN.wav per part under out_dir, plus an inline-timestamped " +
        "output script (script.json for multi-part, part_NN.json for " +
        "single-part) — no sibling _timestamps.json files. Each rendered " +
        "line gains start_ms/end_ms; each part gains wav + " +
        "total_duration_ms; the script gains rendered_utc + " +
        "total_duration_ms. Voice names match by exact then substring " +
        "(case-insensitive) against installed SAPI voices, so legacy " +
        "\"Microsoft David\" resolves to \"Microsoft David Desktop\".")]
    public Task<RenderResult> RenderAudio(
        [Description("Path to the audioscript JSON, relative to the project root or absolute.")]
        string script_path,
        [Description(
            "Optional persona profile path or name. Ignored by the renderer " +
            "(personas are a scripter concern); accepted so director skills " +
            "can pass it without inspecting tool signatures.")]
        string? persona_profile = null,
        [Description(
            "Output directory for WAVs and the rendered script, relative " +
            "to the project root. Conventional: papers/<slug>/podcast/.")]
        string out_dir = "papers/",
        CancellationToken ct = default)
        => renderer.RenderAsync(script_path, persona_profile, out_dir, ct);

    [McpServerTool(Name = "list_voices")]
    [Description(
        "List Windows SAPI voice names available on this machine. Use " +
        "this when configuring presenter voices for render_audio. Cached " +
        "at server startup, so newly installed voices need a restart to " +
        "appear.")]
    public IReadOnlyList<string> ListVoices() => speaker.ListVoices();

    [McpServerTool(Name = "session_status")]
    [Description(
        "Freshness report for a session: which registered artifacts " +
        "exist, their last-modified times, and whether each is stale " +
        "relative to the input papers it was derived from. Use this to " +
        "decide whether to re-run extract / re-render audio after the " +
        "user changes a selection or a paper.md gets re-extracted.")]
    public SessionStatusResult SessionStatus(
        [Description("Session id returned by start_session.")]
        string session)
    {
        var state = sessions.Read(session);
        // We don't know which papers each artifact came from without
        // reading the .spans.json — for now report mtimes and let the
        // caller compare against ListPapers() if it cares about staleness
        // against specific inputs. (Cheap to extend later: read spans,
        // resolve slugs to legacy/new source mtimes, populate stale_against.)
        var statuses = state.Artifacts.Select(rel =>
        {
            var abs = Path.Combine(root.Path, rel);
            var exists = File.Exists(abs);
            DateTime? mtime = exists ? File.GetLastWriteTimeUtc(abs) : null;
            return new ArtifactStatus(rel, exists, mtime, []);
        }).ToList();
        return new SessionStatusResult(state, statuses);
    }
}
