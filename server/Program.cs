using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using PaperCoach.Server.Services;
using Tts;

var builder = WebApplication.CreateBuilder(args);

// Repo root for all paper I/O. Defaults to cwd so `dotnet run` from the
// project root "just works"; the start-servers.bat wrapper sets the env
// var explicitly so launch dir doesn't matter.
var repoRoot = Environment.GetEnvironmentVariable("PAPER_COACH_ROOT")
    ?? Directory.GetCurrentDirectory();
repoRoot = Path.GetFullPath(repoRoot);

builder.Services.AddSingleton(new RepoRoot(repoRoot));
builder.Services.AddSingleton<Workspace>();
builder.Services.AddSingleton<SessionStore>();
builder.Services.AddSingleton<Extractor>();
builder.Services.AddSingleton<PartPlanner>();
builder.Services.AddSingleton<AudioRenderer>();
// Speaker is the shared SAPI wrapper. Cheap to construct (voice probe
// happens once in its ctor), so singleton is fine.
builder.Services.AddSingleton<Speaker>();

// Snake-case JSON matches the project convention (paper.meta.json,
// composed.spans.json, etc.) and is what the MCP tools return — same
// shape Claude will see in artifact files. Applied to both /api/* and
// MCP tool inputs/outputs so callers don't see a casing surprise crossing
// transports.
var jsonOptions = new JsonSerializerOptions
{
    PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
    PropertyNameCaseInsensitive = true,
    WriteIndented = true,
    // MCP marks the options read-only at startup; without an explicit
    // resolver MakeReadOnly() throws because trim-safe defaults assume one.
    // Reflection-based resolver matches the implicit web-API default.
    TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
};

builder.Services.AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly(serializerOptions: jsonOptions);

builder.Services.ConfigureHttpJsonOptions(o =>
{
    o.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
    o.SerializerOptions.WriteIndented = true;
});

var app = builder.Build();

app.Logger.LogInformation("paper-coach root: {Root}", repoRoot);

app.MapMcp("/mcp");

// Liveness probe — start-servers.bat polls this to know when the server
// is up before it backgrounds itself.
app.MapGet("/api/health", (RepoRoot root) =>
    Results.Ok(new { ok = true, root = root.Path }));

app.Run("http://localhost:6000");

/// <summary>
/// Project root path passed via DI so services don't all re-read the env
/// var. Wrapped in a record so the type system distinguishes it from any
/// other string in the graph.
/// </summary>
public sealed record RepoRoot(string Path);
