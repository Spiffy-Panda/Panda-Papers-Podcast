using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using PaperCoach.Server.Models;

namespace PaperCoach.Server.Services;

/// <summary>
/// Workspace sessions live at papers/_workspace/&lt;id&gt;/session.json.
/// One session per chat thread, by convention — the director skill creates
/// one per user-driven exploration so artifacts (composed.md, script.json,
/// etc.) can be grouped and re-derived without colliding across threads.
/// </summary>
public sealed class SessionStore(RepoRoot root, ILogger<SessionStore> log)
{
    private static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        WriteIndented = true,
        PropertyNameCaseInsensitive = true,
    };

    public string WorkspaceRoot =>
        Path.Combine(root.Path, "papers", "_workspace");

    public string SessionDir(string id) =>
        Path.Combine(WorkspaceRoot, id);

    public string SessionFile(string id) =>
        Path.Combine(SessionDir(id), "session.json");

    public SessionRef Start(string? name)
    {
        var id = NewId();
        var dir = SessionDir(id);
        Directory.CreateDirectory(dir);

        var now = DateTime.UtcNow;
        var state = new SessionState(
            Id: id,
            Name: name,
            CreatedUtc: now,
            UpdatedUtc: now,
            Selection: [],
            Artifacts: []);
        Write(state);

        log.LogInformation("Started session {Id} (name={Name}) at {Dir}", id, name, dir);
        return new SessionRef(id, dir, now);
    }

    /// <summary>
    /// All known sessions, sorted by updated_utc descending — newest first
    /// is the order a director skill almost always wants. Skips dirs that
    /// don't have a parseable session.json rather than failing the whole
    /// call (a half-written session shouldn't break enumeration).
    /// </summary>
    public IReadOnlyList<SessionState> List()
    {
        if (!Directory.Exists(WorkspaceRoot)) return [];

        var sessions = new List<SessionState>();
        foreach (var dir in Directory.EnumerateDirectories(WorkspaceRoot))
        {
            var file = Path.Combine(dir, "session.json");
            if (!File.Exists(file)) continue;
            try
            {
                var state = JsonSerializer.Deserialize<SessionState>(
                    File.ReadAllText(file), Json);
                if (state is not null) sessions.Add(state);
            }
            catch (Exception ex)
            {
                log.LogWarning(ex,
                    "Skipping unreadable session at {Path}", file);
            }
        }
        return sessions
            .OrderByDescending(s => s.UpdatedUtc)
            .ToList();
    }

    public SessionState Read(string id)
    {
        var path = SessionFile(id);
        if (!File.Exists(path))
            throw new FileNotFoundException(
                $"Session '{id}' not found at {path}", path);
        var state = JsonSerializer.Deserialize<SessionState>(
            File.ReadAllText(path), Json)
            ?? throw new InvalidOperationException(
                $"Session file '{path}' is empty or unparseable.");
        return state;
    }

    public SessionState Write(SessionState state)
    {
        var path = SessionFile(state.Id);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var touched = state with { UpdatedUtc = DateTime.UtcNow };
        File.WriteAllText(path, JsonSerializer.Serialize(touched, Json));
        return touched;
    }

    /// <summary>
    /// Update the session's selection. Slugs without prefix replace the
    /// selection; +slug adds, -slug removes. Mixing modes (replacement and
    /// delta) in one call is rejected — too easy to footgun.
    /// </summary>
    public SessionState Select(string id, IReadOnlyList<string> slugs)
    {
        var state = Read(id);
        var hasDelta = slugs.Any(s => s.StartsWith('+') || s.StartsWith('-'));
        var hasReplace = slugs.Any(s => !s.StartsWith('+') && !s.StartsWith('-'));
        if (hasDelta && hasReplace)
            throw new ArgumentException(
                "select: mix of plain and +/- prefixed slugs not allowed. " +
                "Use all-plain to replace, or all-prefixed to delta.");

        IReadOnlyList<string> next;
        if (hasDelta)
        {
            var set = new List<string>(state.Selection);
            foreach (var s in slugs)
            {
                if (s.StartsWith('+'))
                {
                    var slug = s[1..];
                    if (!set.Contains(slug, StringComparer.OrdinalIgnoreCase))
                        set.Add(slug);
                }
                else if (s.StartsWith('-'))
                {
                    var slug = s[1..];
                    set.RemoveAll(x =>
                        string.Equals(x, slug, StringComparison.OrdinalIgnoreCase));
                }
            }
            next = set;
        }
        else
        {
            next = slugs.ToList();
        }

        return Write(state with { Selection = next });
    }

    public SessionState RegisterArtifact(string id, string relativePath)
    {
        var state = Read(id);
        if (state.Artifacts.Contains(relativePath))
            return state;
        var artifacts = new List<string>(state.Artifacts) { relativePath };
        return Write(state with { Artifacts = artifacts });
    }

    /// <summary>
    /// Compact, sortable, opaque-enough id. Format: s_YYYYMMDDHHMMSS_xxxx
    /// — date for human grokkability, 4 hex chars to avoid same-second
    /// collisions when the user starts two sessions back-to-back.
    /// </summary>
    private static string NewId()
    {
        var ts = DateTime.UtcNow.ToString("yyyyMMddHHmmss");
        Span<byte> bytes = stackalloc byte[2];
        RandomNumberGenerator.Fill(bytes);
        var sb = new StringBuilder("s_").Append(ts).Append('_');
        foreach (var b in bytes) sb.Append(b.ToString("x2"));
        return sb.ToString();
    }
}
