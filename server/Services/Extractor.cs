using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using PaperCoach.Server.Models;

namespace PaperCoach.Server.Services;

/// <summary>
/// Pulls named sections from selected papers into a single composed.md
/// under the session dir. Side-output: composed.spans.json (which
/// (slug, section_id) maps to which line range) and composed.md.sha256
/// (cheap freshness check for session_status).
/// </summary>
public sealed class Extractor(
    RepoRoot root,
    Workspace workspace,
    SessionStore sessions,
    ILogger<Extractor> log)
{
    private static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        WriteIndented = true,
    };

    public ExtractResult Extract(
        string sessionId,
        IReadOnlyList<string> slugs,
        IReadOnlyList<string> sections,
        string into)
    {
        if (slugs.Count == 0)
            throw new ArgumentException("extract: slugs must not be empty.");
        if (sections.Count == 0)
            throw new ArgumentException("extract: sections must not be empty.");

        var session = sessions.Read(sessionId);
        var outPath = ResolveSessionPath(sessionId, into);
        Directory.CreateDirectory(Path.GetDirectoryName(outPath)!);

        var sb = new StringBuilder();
        var spans = new List<ExtractSpan>();
        var missing = new List<string>();
        var line = 1;

        foreach (var slug in slugs)
        {
            var detail = workspace.Inspect(slug, sections);
            if (detail is null)
            {
                missing.Add($"{slug}");
                continue;
            }

            // Paper header, so a reader can tell where one ends and the next
            // starts. Counts as one line in the spans coordinate system.
            sb.AppendLine($"# {detail.Listing.Meta.Title} ({slug})");
            line++;
            sb.AppendLine();
            line++;

            var bodies = detail.Bodies
                ?? throw new InvalidOperationException(
                    $"Workspace returned null bodies for {slug} despite sections={string.Join(",", sections)}.");

            foreach (var wanted in sections)
            {
                var body = bodies.FirstOrDefault(b =>
                    string.Equals(b.Id, wanted, StringComparison.OrdinalIgnoreCase));
                if (body is null)
                {
                    missing.Add($"{slug}#{wanted}");
                    continue;
                }

                var startLine = line;
                sb.AppendLine($"## {body.Title}");
                line++;
                sb.AppendLine();
                line++;

                foreach (var para in body.Paragraphs)
                {
                    sb.AppendLine(para.Text);
                    line++;
                    sb.AppendLine();
                    line++;
                }

                spans.Add(new ExtractSpan(
                    Slug: slug,
                    SectionId: body.Id,
                    StartLine: startLine,
                    EndLine: line - 1,
                    ParagraphIds: body.Paragraphs.Select(p => p.Id).ToList()));
            }
        }

        var composed = sb.ToString();
        File.WriteAllText(outPath, composed);
        var sha = Sha256(composed);
        File.WriteAllText(outPath + ".sha256", sha);

        var spansPath = Path.ChangeExtension(outPath, ".spans.json");
        File.WriteAllText(spansPath, JsonSerializer.Serialize(new
        {
            source = "extract",
            session = sessionId,
            slugs,
            sections,
            spans,
        }, Json));

        var rel = Path.GetRelativePath(root.Path, outPath).Replace('\\', '/');
        sessions.RegisterArtifact(sessionId, rel);
        sessions.RegisterArtifact(sessionId, rel + ".sha256");
        sessions.RegisterArtifact(sessionId,
            Path.GetRelativePath(root.Path, spansPath).Replace('\\', '/'));

        log.LogInformation(
            "extract: session={Session} slugs={Slugs} sections={Sections} → {Path} ({Lines} lines, {Missing} missing)",
            sessionId, string.Join(",", slugs), string.Join(",", sections),
            rel, line - 1, missing.Count);

        return new ExtractResult(
            ComposedPath: rel,
            Sha256: sha,
            LineCount: line - 1,
            Spans: spans,
            Missing: missing);
    }

    public ExtractResult Combine(
        string sessionId,
        IReadOnlyList<string> files,
        string into)
    {
        if (files.Count == 0)
            throw new ArgumentException("combine: files must not be empty.");

        sessions.Read(sessionId); // existence check; throws if missing
        var outPath = ResolveSessionPath(sessionId, into);
        Directory.CreateDirectory(Path.GetDirectoryName(outPath)!);

        var sb = new StringBuilder();
        var spans = new List<ExtractSpan>();
        var missing = new List<string>();
        var line = 1;

        foreach (var rel in files)
        {
            var abs = Path.IsPathRooted(rel) ? rel : Path.Combine(root.Path, rel);
            if (!File.Exists(abs))
            {
                missing.Add(rel);
                continue;
            }

            var content = File.ReadAllText(abs);
            var start = line;
            sb.Append(content);
            if (!content.EndsWith('\n'))
            {
                sb.AppendLine();
                line++;
            }
            line += content.Count(c => c == '\n');

            // Combine doesn't know about sections; record a single span per
            // file so session_status can still attribute regions to inputs.
            spans.Add(new ExtractSpan(
                Slug: Path.GetFileNameWithoutExtension(abs),
                SectionId: "(file)",
                StartLine: start,
                EndLine: line - 1,
                ParagraphIds: []));
        }

        var composed = sb.ToString();
        File.WriteAllText(outPath, composed);
        var sha = Sha256(composed);
        File.WriteAllText(outPath + ".sha256", sha);

        var spansPath = Path.ChangeExtension(outPath, ".spans.json");
        File.WriteAllText(spansPath, JsonSerializer.Serialize(new
        {
            source = "combine",
            session = sessionId,
            files,
            spans,
        }, Json));

        var relOut = Path.GetRelativePath(root.Path, outPath).Replace('\\', '/');
        sessions.RegisterArtifact(sessionId, relOut);
        sessions.RegisterArtifact(sessionId, relOut + ".sha256");
        sessions.RegisterArtifact(sessionId,
            Path.GetRelativePath(root.Path, spansPath).Replace('\\', '/'));

        return new ExtractResult(
            ComposedPath: relOut,
            Sha256: sha,
            LineCount: line - 1,
            Spans: spans,
            Missing: missing);
    }

    private string ResolveSessionPath(string sessionId, string into)
    {
        // Caller may pass a bare filename ("composed.md") or a path
        // relative to the session dir. Absolute paths outside the session
        // dir are rejected — extract should never overwrite arbitrary files.
        if (Path.IsPathRooted(into))
            throw new ArgumentException(
                $"extract/combine: 'into' must be relative to the session dir, got absolute path '{into}'.");
        var sessionDir = sessions.SessionDir(sessionId);
        var full = Path.GetFullPath(Path.Combine(sessionDir, into));
        if (!full.StartsWith(sessionDir, StringComparison.OrdinalIgnoreCase))
            throw new ArgumentException(
                $"extract/combine: 'into' escapes the session dir ('{into}').");
        return full;
    }

    private static string Sha256(string content)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(content));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}
