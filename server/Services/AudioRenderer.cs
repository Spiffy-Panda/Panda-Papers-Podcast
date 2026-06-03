using Microsoft.Extensions.Logging;
using PaperCoach.Server.Models;

namespace PaperCoach.Server.Services;

/// <summary>
/// render_audio is wired but not yet implemented. The contract is the
/// legacy dialog-JSON schema (input/&lt;slug&gt;/part_NN.json) with the four
/// polish items from memory/new-mode-audioscript.md applied: split voice
/// from persona, paper_slug instead of paper_source path, inline timestamps,
/// inline part_of. The TTS plumbing (two-voice alternation through the
/// shared Speaker library) is the actual work — the schema is settled.
/// </summary>
public sealed class AudioRenderer(ILogger<AudioRenderer> log)
{
    public RenderResult Render(string scriptPath, string? personaProfile, string outDir)
    {
        log.LogInformation(
            "render_audio called (script={Script}, persona={Persona}, out={Out}) — stubbed.",
            scriptPath, personaProfile, outDir);
        return new RenderResult(
            Ok: false,
            Error: "not_implemented",
            Reason: "render_audio is wire-only. Contract: polished legacy dialog-JSON schema (see memory/new-mode-audioscript.md). TTS plumbing pending — ships with script-to-audio skill.",
            NotImplemented: true);
    }
}
