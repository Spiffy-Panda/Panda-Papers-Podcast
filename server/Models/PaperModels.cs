using System.Text.Json.Serialization;

namespace PaperCoach.Server.Models;

/// <summary>
/// Bibliographic metadata for a paper, matching input/paper_json_spec.md
/// `meta` shape. Used for both new-layout paper.meta.json and legacy
/// input/&lt;slug&gt;_paper.json.
/// </summary>
public sealed record PaperMeta(
    string Title,
    IReadOnlyList<string> Authors,
    string? Journal,
    int? Year,
    string? Doi,
    string? Pmcid,
    string? SourceUrl,
    string? License);

/// <summary>
/// One paper as it shows up in list_papers — slug plus enough metadata for
/// the director to pick from. Flags note which artifacts exist on disk.
/// </summary>
public sealed record PaperListing(
    string Slug,
    PaperMeta Meta,
    string Source,           // "new" | "legacy"
    bool HasMd,
    bool HasMeta,
    bool HasGraph,
    bool HasHighlights,
    int? ParagraphCount);

public sealed record SectionInfo(
    string Id,
    string Title,
    int ParagraphCount,
    IReadOnlyList<int> ParagraphIds);

public sealed record SectionBody(
    string Id,
    string Title,
    IReadOnlyList<Paragraph> Paragraphs);

public sealed record Paragraph(int Id, string Text);

public sealed record PaperDetail(
    PaperListing Listing,
    IReadOnlyList<SectionInfo> Sections,
    IReadOnlyList<SectionBody>? Bodies);

/// <summary>
/// Workspace session — one chat-driven working set of papers and the
/// composed artifacts derived from it. Lives at
/// papers/_workspace/&lt;id&gt;/session.json.
/// </summary>
public sealed record SessionState(
    string Id,
    string? Name,
    DateTime CreatedUtc,
    DateTime UpdatedUtc,
    IReadOnlyList<string> Selection,
    IReadOnlyList<string> Artifacts);

public sealed record SessionRef(string Id, string Dir, DateTime CreatedUtc);

public sealed record ExtractSpan(
    string Slug,
    string SectionId,
    int StartLine,
    int EndLine,
    IReadOnlyList<int> ParagraphIds);

public sealed record ExtractResult(
    string ComposedPath,
    string Sha256,
    int LineCount,
    IReadOnlyList<ExtractSpan> Spans,
    IReadOnlyList<string> Missing);

public sealed record RenderResult(
    bool Ok,
    string? Error = null,
    string? Reason = null,
    [property: JsonPropertyName("not_implemented")] bool NotImplemented = false,
    string? ScriptPath = null,
    IReadOnlyList<string>? WavPaths = null,
    double? TotalDurationMs = null,
    int? PartsRendered = null);

public sealed record ArtifactStatus(
    string Path,
    bool Exists,
    DateTime? Mtime,
    IReadOnlyList<string> StaleAgainst);

public sealed record SessionStatusResult(
    SessionState Session,
    IReadOnlyList<ArtifactStatus> Artifacts);

/// <summary>
/// One planned podcast part — paragraph IDs from the paper that should be
/// covered, plus the sections they came from. Ported from
/// init_podcast.py's split_paragraphs_into_parts; same shape as the
/// legacy state file's parts_plan[] entries so a scripter can feed this
/// straight into the new pipeline without translating.
/// </summary>
public sealed record PlannedPart(
    int PartNumber,
    IReadOnlyList<int> ParagraphIds,
    IReadOnlyList<string> SectionIds,
    IReadOnlyList<string> SectionTitles);
