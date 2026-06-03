using System.Text.Json;
using Microsoft.Extensions.Logging;
using PaperCoach.Server.Models;

namespace PaperCoach.Server.Services;

/// <summary>
/// Paper enumeration over both the new layout (papers/&lt;slug&gt;/) and the
/// legacy one (input/&lt;slug&gt;_paper.json). New-layout wins on slug
/// collision — legacy is what you migrated from.
/// </summary>
public sealed class Workspace(RepoRoot root, ILogger<Workspace> log)
{
    private static readonly JsonSerializerOptions Json = new()
    {
        // paper.json files use snake_case keys (source_url, pmcid, etc.);
        // PaperMeta records use PascalCase properties. SnakeCaseLower policy
        // is what bridges them.
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
    };

    public IReadOnlyList<PaperListing> ListPapers()
    {
        var seen = new Dictionary<string, PaperListing>(StringComparer.OrdinalIgnoreCase);

        foreach (var listing in ScanNewLayout())
            seen[listing.Slug] = listing;

        foreach (var listing in ScanLegacy())
            seen.TryAdd(listing.Slug, listing);

        return seen.Values
            .OrderBy(p => p.Slug, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }

    public PaperListing? FindPaper(string slug) =>
        ListPapers().FirstOrDefault(p =>
            string.Equals(p.Slug, slug, StringComparison.OrdinalIgnoreCase));

    /// <summary>
    /// Section index for a paper. Uses paper.md + paper.spans.json when
    /// available, falls back to the legacy paper.json otherwise.
    /// </summary>
    public PaperDetail? Inspect(string slug, IReadOnlyList<string>? sections = null)
    {
        var listing = FindPaper(slug);
        if (listing is null) return null;

        var (sectionInfos, bodies) = listing.Source == "legacy"
            ? ReadLegacySections(slug, sections)
            : ReadNewSections(slug, sections);

        return new PaperDetail(listing, sectionInfos, bodies);
    }

    // ── scanners ───────────────────────────────────────────────────────

    private IEnumerable<PaperListing> ScanNewLayout()
    {
        var papersDir = Path.Combine(root.Path, "papers");
        if (!Directory.Exists(papersDir)) yield break;

        foreach (var dir in Directory.EnumerateDirectories(papersDir))
        {
            var slug = Path.GetFileName(dir);
            if (slug.StartsWith('_')) continue; // _workspace/ etc.

            var metaPath = Path.Combine(dir, "paper.meta.json");
            if (!File.Exists(metaPath)) continue;

            PaperMeta? meta;
            try
            {
                meta = JsonSerializer.Deserialize<PaperMeta>(
                    File.ReadAllText(metaPath), Json);
            }
            catch (Exception ex)
            {
                log.LogWarning(ex, "Failed to read paper.meta.json for {Slug}", slug);
                continue;
            }
            if (meta is null) continue;

            yield return new PaperListing(
                Slug: slug,
                Meta: meta,
                Source: "new",
                HasMd: File.Exists(Path.Combine(dir, "paper.md")),
                HasMeta: true,
                HasGraph: File.Exists(Path.Combine(dir, "graph.cypher")),
                HasHighlights: File.Exists(Path.Combine(dir, "highlights.json")),
                ParagraphCount: null);
        }
    }

    private IEnumerable<PaperListing> ScanLegacy()
    {
        var inputDir = Path.Combine(root.Path, "input");
        if (!Directory.Exists(inputDir)) yield break;

        foreach (var file in Directory.EnumerateFiles(inputDir, "*_paper.json"))
        {
            var slug = Path.GetFileNameWithoutExtension(file);
            if (slug.EndsWith("_paper", StringComparison.OrdinalIgnoreCase))
                slug = slug[..^"_paper".Length];
            slug = slug.ToLowerInvariant(); // ODESteer_paper.json → odesteer

            var (meta, paraCount) = ReadLegacyMetaAndCount(file);
            if (meta is null) continue;

            yield return new PaperListing(
                Slug: slug,
                Meta: meta,
                Source: "legacy",
                HasMd: false,
                HasMeta: false,
                HasGraph: false,
                HasHighlights: false,
                ParagraphCount: paraCount);
        }
    }

    private (PaperMeta?, int?) ReadLegacyMetaAndCount(string path)
    {
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var root = doc.RootElement;
            if (!root.TryGetProperty("meta", out var metaEl))
                return (null, null);

            var meta = JsonSerializer.Deserialize<PaperMeta>(metaEl.GetRawText(), Json);
            int? count = null;
            if (root.TryGetProperty("sections", out var secs) &&
                secs.ValueKind == JsonValueKind.Array)
            {
                count = 0;
                foreach (var sec in secs.EnumerateArray())
                {
                    if (sec.TryGetProperty("paragraphs", out var paras) &&
                        paras.ValueKind == JsonValueKind.Array)
                    {
                        count += paras.GetArrayLength();
                    }
                }
            }
            return (meta, count);
        }
        catch (Exception ex)
        {
            log.LogWarning(ex, "Failed to parse legacy paper at {Path}", path);
            return (null, null);
        }
    }

    // ── section readers ────────────────────────────────────────────────

    private (IReadOnlyList<SectionInfo>, IReadOnlyList<SectionBody>?)
        ReadLegacySections(string slug, IReadOnlyList<string>? wanted)
    {
        // Mirror the slug → file resolution used in ScanLegacy: lowercased
        // slug.json with the _paper suffix, but also tolerate the cased
        // original (ODESteer_paper.json).
        var inputDir = Path.Combine(root.Path, "input");
        var path = Directory.EnumerateFiles(inputDir, "*_paper.json")
            .FirstOrDefault(p =>
            {
                var s = Path.GetFileNameWithoutExtension(p);
                if (s.EndsWith("_paper", StringComparison.OrdinalIgnoreCase))
                    s = s[..^"_paper".Length];
                return string.Equals(s, slug, StringComparison.OrdinalIgnoreCase);
            });
        if (path is null) return ([], null);

        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        if (!doc.RootElement.TryGetProperty("sections", out var secs))
            return ([], null);

        var infos = new List<SectionInfo>();
        var bodies = wanted is null ? null : new List<SectionBody>();
        var wantedSet = wanted is null
            ? null
            : new HashSet<string>(wanted, StringComparer.OrdinalIgnoreCase);

        foreach (var sec in secs.EnumerateArray())
        {
            var id = sec.GetProperty("id").GetString() ?? "";
            var title = sec.GetProperty("title").GetString() ?? id;
            var paraIds = new List<int>();
            var paragraphs = new List<Paragraph>();

            if (sec.TryGetProperty("paragraphs", out var paras))
            {
                foreach (var p in paras.EnumerateArray())
                {
                    var pid = p.GetProperty("id").GetInt32();
                    var text = p.GetProperty("text").GetString() ?? "";
                    paraIds.Add(pid);
                    paragraphs.Add(new Paragraph(pid, text));
                }
            }

            infos.Add(new SectionInfo(id, title, paraIds.Count, paraIds));
            if (bodies is not null &&
                wantedSet!.Contains(id))
            {
                bodies.Add(new SectionBody(id, title, paragraphs));
            }
        }

        return (infos, bodies);
    }

    private (IReadOnlyList<SectionInfo>, IReadOnlyList<SectionBody>?)
        ReadNewSections(string slug, IReadOnlyList<string>? wanted)
    {
        // New layout: paper.md is the canonical text, paper.spans.json
        // indexes section → line range / paragraph ids. Until pdf-sidecar
        // is producing those, return an empty index rather than fabricating
        // one — caller can fall back to inspect_paper on the legacy copy
        // if one exists.
        var dir = Path.Combine(root.Path, "papers", slug);
        var spansPath = Path.Combine(dir, "paper.spans.json");
        if (!File.Exists(spansPath)) return ([], null);

        // The shape of paper.spans.json is owned by pdf-to-markdown
        // (planned). When that skill ships, plumb it through here.
        log.LogInformation(
            "paper.spans.json exists for {Slug} but new-layout section " +
            "reader is not implemented yet (pending pdf-to-markdown schema).",
            slug);
        return ([], null);
    }
}
