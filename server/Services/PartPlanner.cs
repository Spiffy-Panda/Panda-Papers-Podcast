using Microsoft.Extensions.Logging;
using PaperCoach.Server.Models;

namespace PaperCoach.Server.Services;

/// <summary>
/// Section-aware podcast part splitter, ported from init_podcast.py's
/// split_paragraphs_into_parts. Accumulates whole sections into a part
/// until adding the next section would exceed max-per-part (and the
/// current part already has min-per-part), then flushes. Sections longer
/// than max get sliced. Trailing under-min parts merge into the previous.
///
/// Pure function — does not write any files. The caller (podcast-scripter
/// SKILL.md) decides whether to persist the result.
/// </summary>
public sealed class PartPlanner(Workspace workspace, ILogger<PartPlanner> log)
{
    public IReadOnlyList<PlannedPart> Plan(
        string slug, int minPerPart = 3, int maxPerPart = 7)
    {
        if (minPerPart < 1)
            throw new ArgumentOutOfRangeException(nameof(minPerPart),
                $"minPerPart must be ≥1, got {minPerPart}.");
        if (maxPerPart < minPerPart)
            throw new ArgumentOutOfRangeException(nameof(maxPerPart),
                $"maxPerPart ({maxPerPart}) must be ≥ minPerPart ({minPerPart}).");

        var detail = workspace.Inspect(slug)
            ?? throw new ArgumentException(
                $"plan_parts: unknown slug '{slug}'.", nameof(slug));

        var sections = detail.Sections;
        if (sections.Count == 0)
        {
            // New-layout paper without a working section reader yet, or
            // a malformed legacy paper. Surface that rather than returning
            // an empty plan that looks like a successful split.
            log.LogWarning(
                "plan_parts: {Slug} has no readable sections — returning empty plan.",
                slug);
            return [];
        }

        var titleMap = sections.ToDictionary(s => s.Id, s => s.Title);
        var parts = new List<(List<int> Paras, List<string> SecIds)>();
        var current = (Paras: new List<int>(), SecIds: new List<string>());

        foreach (var sec in sections)
        {
            // If adding this section would overshoot AND the current part
            // already has enough, flush before adding it. Matches the
            // Python heuristic exactly.
            if (current.Paras.Count > 0
                && current.Paras.Count + sec.ParagraphIds.Count > maxPerPart
                && current.Paras.Count >= minPerPart)
            {
                parts.Add(current);
                current = (new List<int>(), new List<string>());
            }

            current.Paras.AddRange(sec.ParagraphIds);
            if (!current.SecIds.Contains(sec.Id))
                current.SecIds.Add(sec.Id);

            // Large section: slice into max-sized chunks, keeping the
            // section id list intact so each chunk records its origin.
            while (current.Paras.Count > maxPerPart)
            {
                var chunk = current.Paras.Take(maxPerPart).ToList();
                parts.Add((chunk, new List<string>(current.SecIds)));
                current.Paras = current.Paras.Skip(maxPerPart).ToList();
            }
        }

        if (current.Paras.Count > 0)
            parts.Add(current);

        // Merge a too-small trailing part back into its predecessor.
        // Only the LAST part is special-cased — interior under-min parts
        // shouldn't happen given the flush rule above, but if they did
        // we'd leave them alone (deliberate, matches Python).
        var merged = new List<(List<int> Paras, List<string> SecIds)>();
        foreach (var part in parts)
        {
            if (merged.Count > 0 && part.Paras.Count < minPerPart)
            {
                var prev = merged[^1];
                prev.Paras.AddRange(part.Paras);
                foreach (var sid in part.SecIds)
                    if (!prev.SecIds.Contains(sid))
                        prev.SecIds.Add(sid);
            }
            else
            {
                merged.Add(part);
            }
        }

        return merged
            .Select((p, i) => new PlannedPart(
                PartNumber: i + 1,
                ParagraphIds: p.Paras,
                SectionIds: p.SecIds,
                SectionTitles: p.SecIds.Select(sid => titleMap[sid]).ToList()))
            .ToList();
    }
}
