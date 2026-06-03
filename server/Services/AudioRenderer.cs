using System.Runtime.Versioning;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.Logging;
using PaperCoach.Server.Models;
using Tts;

namespace PaperCoach.Server.Services;

/// <summary>
/// Renders a podcast audioscript to per-part WAV files via the shared TTS
/// Speaker. Contract spelled out in PIPELINE-DECISIONS.md §5 — accepts both
/// multi-part script.json and legacy single-part part_NN.json shapes,
/// emits stable-named part_NN.wav files plus an inline-timestamped output
/// script (no sibling _timestamps.json files).
/// </summary>
[SupportedOSPlatform("windows")]
public sealed class AudioRenderer(
    RepoRoot root,
    Speaker speaker,
    ILogger<AudioRenderer> log)
{
    private static readonly JsonSerializerOptions JsonWrite = new()
    {
        WriteIndented = true,
        // Preserve original casing on pass-through fields. The polished
        // schema uses snake_case throughout (paper_slug, source_paragraphs)
        // so we serialize JsonNode round-trips with their original keys.
    };

    public async Task<RenderResult> RenderAsync(
        string scriptPath,
        string? personaProfile,
        string outDir,
        CancellationToken ct)
    {
        if (personaProfile is not null)
            // Persona profiles aren't a renderer concern — they belong to
            // the scripter. We log but don't error so a director skill can
            // pass the same arg shape regardless of which side honors it.
            log.LogDebug("render_audio: persona_profile={Persona} ignored (scripter concern)",
                personaProfile);

        var absScript = ResolveUnderRoot(scriptPath);
        if (!File.Exists(absScript))
            return new RenderResult(
                Ok: false,
                Error: "script_not_found",
                Reason: $"No audioscript at {absScript}.");

        var absOut = ResolveUnderRoot(outDir);
        Directory.CreateDirectory(absOut);

        // Parse the script as a mutable tree so we can pass through unknown
        // fields untouched and just bolt timestamps onto the spots we care
        // about. JsonDocument would be read-only.
        JsonNode? doc;
        try
        {
            await using var fs = File.OpenRead(absScript);
            doc = await JsonNode.ParseAsync(fs, cancellationToken: ct);
        }
        catch (JsonException ex)
        {
            return new RenderResult(
                Ok: false,
                Error: "script_malformed",
                Reason: $"Could not parse {absScript}: {ex.Message}");
        }
        if (doc is not JsonObject rootObj)
            return new RenderResult(
                Ok: false,
                Error: "script_malformed",
                Reason: "Audioscript root must be a JSON object.");

        var isMultiPart = rootObj["parts"] is JsonArray;
        var partsArray = isMultiPart
            ? (JsonArray)rootObj["parts"]!
            : new JsonArray(rootObj); // legacy single-part: wrap so the loop is uniform

        var topPause = ReadDouble(rootObj, "pause_between_ms") ?? 500.0;
        var topRate = ReadInt(rootObj, "rate") ?? 0;

        var tempDir = Path.Combine(Path.GetTempPath(),
            $"paper-coach-render-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);

        // Voice-name resolver: legacy scripts say "Microsoft David" but SAPI
        // installs voices as "Microsoft David Desktop". The shared Speaker
        // does exact match only (intentional — Voice Coach's UX is "use the
        // string SAPI gave you"); here we add substring fallback to keep the
        // legacy on-disk parts renderable without rewriting them.
        var installedVoices = speaker.ListVoices();

        var wavPaths = new List<string>();
        var totalDurationMs = 0.0;
        try
        {
            for (var pi = 0; pi < partsArray.Count; pi++)
            {
                if (partsArray[pi] is not JsonObject part)
                    return new RenderResult(
                        Ok: false,
                        Error: "part_malformed",
                        Reason: $"parts[{pi}] is not a JSON object.");

                var partNumber = ReadInt(part, "part_number")
                    ?? ReadPartOfN(part)
                    ?? (pi + 1);
                var partPause = ReadDouble(part, "pause_between_ms") ?? topPause;
                var partRate = ReadInt(part, "rate") ?? topRate;

                if (part["lines"] is not JsonArray lines || lines.Count == 0)
                    return new RenderResult(
                        Ok: false,
                        Error: "part_empty",
                        Reason: $"parts[{pi}] has no lines.");

                var wavName = $"part_{partNumber:D2}.wav";
                var wavOut = Path.Combine(absOut, wavName);
                var partDuration = await RenderPartAsync(
                    lines, partPause, partRate, tempDir, wavOut,
                    installedVoices, ct);

                // Inline timestamps + WAV ref onto the part itself. The
                // input fields stay; we just add ours.
                part["wav"] = wavName;
                part["total_duration_ms"] = Math.Round(partDuration, 1);

                wavPaths.Add(Path.GetRelativePath(root.Path, wavOut).Replace('\\', '/'));
                totalDurationMs += partDuration;
            }
        }
        catch (OperationCanceledException)
        {
            return new RenderResult(
                Ok: false,
                Error: "cancelled",
                Reason: "Render cancelled.");
        }
        catch (Exception ex)
        {
            log.LogError(ex, "render_audio failed mid-part");
            return new RenderResult(
                Ok: false,
                Error: "render_failed",
                Reason: ex.Message);
        }
        finally
        {
            TryCleanupTemp(tempDir);
        }

        // Output script: same shape as input plus rendered_utc /
        // total_duration_ms / per-part wav + per-line start_ms/end_ms.
        rootObj["rendered_utc"] = DateTime.UtcNow.ToString("o");
        rootObj["total_duration_ms"] = Math.Round(totalDurationMs, 1);

        var outScriptName = isMultiPart
            ? "script.json"
            : $"part_{ReadInt(partsArray[0]!.AsObject(), "part_number") ?? 1:D2}.json";
        var outScriptPath = Path.Combine(absOut, outScriptName);

        await using (var outFs = File.Create(outScriptPath))
        {
            await JsonSerializer.SerializeAsync(outFs, rootObj, JsonWrite, ct);
        }

        return new RenderResult(
            Ok: true,
            ScriptPath: Path.GetRelativePath(root.Path, outScriptPath).Replace('\\', '/'),
            WavPaths: wavPaths,
            TotalDurationMs: Math.Round(totalDurationMs, 1),
            PartsRendered: partsArray.Count);
    }

    private async Task<double> RenderPartAsync(
        JsonArray lines,
        double pauseMs,
        int rate,
        string tempDir,
        string wavOut,
        IReadOnlyList<string> installedVoices,
        CancellationToken ct)
    {
        // Speaker.Rate is the SAPI -10..+10 scale; Speaker.SpeakToFileAsync
        // takes a 0.1..3.0 speed instead. Map back: 0 → 1.0, -5 → 0.5,
        // +10 → 2.0. Conservative — caller's `rate` overrides any per-line
        // speed since the polished schema doesn't expose one.
        var speed = 1.0 + (rate / 10.0);
        speed = Math.Clamp(speed, 0.1, 3.0);

        var lineFiles = new List<string>(lines.Count * 2);
        var currentMs = 0.0;
        WavTools.WavFormat? sharedFmt = null;

        for (var li = 0; li < lines.Count; li++)
        {
            if (lines[li] is not JsonObject line)
                throw new InvalidDataException($"lines[{li}] is not a JSON object.");

            var voice = (string?)line["voice"]
                ?? throw new InvalidDataException($"lines[{li}] missing voice.");
            var text = (string?)line["text"]
                ?? throw new InvalidDataException($"lines[{li}] missing text.");

            var resolvedVoice = ResolveVoice(voice, installedVoices) ?? voice;
            var linePath = Path.Combine(tempDir,
                $"line_{Guid.NewGuid():N}.wav");
            await speaker.SpeakToFileAsync(text, resolvedVoice, speed, linePath, ct);

            var duration = WavTools.GetDurationMs(linePath);
            line["start_ms"] = Math.Round(currentMs, 1);
            line["end_ms"] = Math.Round(currentMs + duration, 1);

            lineFiles.Add(linePath);
            currentMs += duration;

            // Probe format once — SAPI defaults to 22 kHz/16/mono but a
            // user-installed voice can override. First line wins; mismatches
            // surface in Concatenate().
            sharedFmt ??= WavTools.ReadHeader(linePath).Format;

            if (li < lines.Count - 1 && pauseMs > 0)
            {
                var silencePath = Path.Combine(tempDir,
                    $"silence_{Guid.NewGuid():N}.wav");
                WavTools.WriteSilence(silencePath, sharedFmt, pauseMs);
                lineFiles.Add(silencePath);
                currentMs += pauseMs;
            }
        }

        WavTools.Concatenate(lineFiles, wavOut);
        return currentMs;
    }

    /// <summary>
    /// Map a script-declared voice name (e.g. "Microsoft David") to an
    /// actually-installed SAPI voice (e.g. "Microsoft David Desktop"). Exact
    /// match wins; otherwise the first installed voice whose name contains
    /// the requested string (case-insensitive). Returns null if nothing
    /// matches, which falls back to whatever the shared Speaker picks.
    /// </summary>
    private static string? ResolveVoice(string requested, IReadOnlyList<string> installed)
    {
        if (string.IsNullOrWhiteSpace(requested) || installed.Count == 0) return null;
        var exact = installed.FirstOrDefault(v =>
            string.Equals(v, requested, StringComparison.OrdinalIgnoreCase));
        if (exact is not null) return exact;
        return installed.FirstOrDefault(v =>
            v.Contains(requested, StringComparison.OrdinalIgnoreCase));
    }

    private string ResolveUnderRoot(string rel)
    {
        if (Path.IsPathRooted(rel)) return Path.GetFullPath(rel);
        return Path.GetFullPath(Path.Combine(root.Path, rel));
    }

    private static double? ReadDouble(JsonObject obj, string key)
    {
        if (obj[key] is JsonValue v && v.TryGetValue<double>(out var d)) return d;
        if (obj[key] is JsonValue vi && vi.TryGetValue<int>(out var i)) return i;
        return null;
    }

    private static int? ReadInt(JsonObject obj, string key)
    {
        if (obj[key] is JsonValue v && v.TryGetValue<int>(out var i)) return i;
        return null;
    }

    /// <summary>
    /// part_of: {n, total} is the polished schema's way of carrying the
    /// part index. Falls back to null if the field is absent or shaped wrong.
    /// </summary>
    private static int? ReadPartOfN(JsonObject part)
    {
        if (part["part_of"] is JsonObject po) return ReadInt(po, "n");
        return null;
    }

    private void TryCleanupTemp(string tempDir)
    {
        try { Directory.Delete(tempDir, recursive: true); }
        catch (Exception ex)
        {
            // Non-fatal — temp dir will eventually be reaped. Log so a
            // human notices if it leaks repeatedly.
            log.LogDebug(ex, "render_audio: failed to clean up {Temp}", tempDir);
        }
    }
}
