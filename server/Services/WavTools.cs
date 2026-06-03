using System.Text;

namespace PaperCoach.Server.Services;

/// <summary>
/// PCM WAV file helpers — duration probe, silence-fill, concatenation. All
/// operate on the canonical SAPI output (RIFF/WAVE, fmt subchunk, data
/// subchunk, optional trailing chunks ignored). Same approach
/// dialog_to_audio.py used with Python's wave module; rewritten here so
/// the C# pipeline doesn't shell out for PCM byte-shuffling.
/// </summary>
public static class WavTools
{
    /// <summary>
    /// PCM format read from a WAV header. Used to round-trip silence files
    /// and to validate that concatenation inputs are compatible.
    /// </summary>
    public sealed record WavFormat(
        ushort NumChannels,
        uint SampleRate,
        ushort BitsPerSample)
    {
        public uint ByteRate => SampleRate * NumChannels * (uint)(BitsPerSample / 8);
        public ushort BlockAlign => (ushort)(NumChannels * (BitsPerSample / 8));
    }

    /// <summary>
    /// Parse the WAV header at <paramref name="path"/> and return format +
    /// the byte length of the data subchunk. Throws on malformed RIFF/WAVE
    /// or on non-PCM formats — we synthesize via SAPI which always writes
    /// PCM, so anything else is a programmer error worth surfacing loudly.
    /// </summary>
    public static (WavFormat Format, long DataBytes) ReadHeader(string path)
    {
        using var fs = File.OpenRead(path);
        using var br = new BinaryReader(fs, Encoding.ASCII, leaveOpen: false);

        Expect(br, "RIFF");
        _ = br.ReadUInt32(); // file size minus 8 — don't need to validate
        Expect(br, "WAVE");

        WavFormat? format = null;
        long dataBytes = -1;

        // Walk chunks until we've seen both fmt and data. SAPI typically
        // emits fmt then data, but some recorders interleave LIST/INFO
        // chunks; tolerate them by skipping unknowns.
        while (fs.Position < fs.Length - 8)
        {
            var chunkId = Encoding.ASCII.GetString(br.ReadBytes(4));
            var chunkSize = br.ReadUInt32();

            if (chunkId == "fmt ")
            {
                var audioFormat = br.ReadUInt16();
                if (audioFormat != 1)
                    throw new InvalidDataException(
                        $"WAV {path}: expected PCM (audio_format=1), got {audioFormat}.");
                var numChannels = br.ReadUInt16();
                var sampleRate = br.ReadUInt32();
                _ = br.ReadUInt32(); // byte_rate, derived
                _ = br.ReadUInt16(); // block_align, derived
                var bitsPerSample = br.ReadUInt16();
                format = new WavFormat(numChannels, sampleRate, bitsPerSample);

                // fmt subchunks can carry extra trailing bytes (cbSize block).
                // Skip them so we land on the next chunk header cleanly.
                var consumed = 16;
                if (chunkSize > consumed)
                    fs.Seek(chunkSize - consumed, SeekOrigin.Current);
            }
            else if (chunkId == "data")
            {
                dataBytes = chunkSize;
                break; // we know what we need; stop reading
            }
            else
            {
                // Unknown chunk (LIST, INFO, junk, ...) — skip its payload.
                // Round up odd sizes per RIFF spec.
                var skip = chunkSize + (chunkSize & 1);
                fs.Seek(skip, SeekOrigin.Current);
            }
        }

        if (format is null)
            throw new InvalidDataException($"WAV {path}: no fmt subchunk found.");
        if (dataBytes < 0)
            throw new InvalidDataException($"WAV {path}: no data subchunk found.");

        return (format, dataBytes);
    }

    /// <summary>
    /// Duration in milliseconds, computed from data length and byte rate.
    /// </summary>
    public static double GetDurationMs(string path)
    {
        var (fmt, dataBytes) = ReadHeader(path);
        return dataBytes / (double)fmt.ByteRate * 1000.0;
    }

    /// <summary>
    /// Write a WAV file of silence at <paramref name="path"/>, matching the
    /// given format. <paramref name="durationMs"/> is rounded to whole
    /// frames using the sample rate.
    /// </summary>
    public static void WriteSilence(string path, WavFormat format, double durationMs)
    {
        var frames = (uint)Math.Round(format.SampleRate * durationMs / 1000.0);
        var dataBytes = frames * format.BlockAlign;

        using var fs = File.Create(path);
        using var bw = new BinaryWriter(fs, Encoding.ASCII, leaveOpen: false);
        WriteHeader(bw, format, dataBytes);
        // Zero-fill in chunks to keep allocations bounded for long silences.
        var buf = new byte[Math.Min(dataBytes, 64 * 1024)];
        var remaining = dataBytes;
        while (remaining > 0)
        {
            var chunk = (int)Math.Min(buf.Length, remaining);
            bw.Write(buf, 0, chunk);
            remaining -= (uint)chunk;
        }
    }

    /// <summary>
    /// Concatenate <paramref name="inputs"/> into a single WAV at
    /// <paramref name="output"/>. All inputs must share the same format —
    /// throws otherwise. Returns the combined data size in bytes.
    /// </summary>
    public static long Concatenate(IReadOnlyList<string> inputs, string output)
    {
        if (inputs.Count == 0)
            throw new ArgumentException("Concatenate: inputs must not be empty.");

        // Read all headers first so a mismatch fails before we open the
        // output — easier to recover from than half a corrupt file.
        var headers = inputs.Select(p => (Path: p, Header: ReadHeader(p))).ToList();
        var fmt = headers[0].Header.Format;
        foreach (var (path, (otherFmt, _)) in headers.Skip(1))
        {
            if (otherFmt != fmt)
                throw new InvalidDataException(
                    $"Concatenate: format mismatch — {inputs[0]} is " +
                    $"{fmt}, {path} is {otherFmt}.");
        }

        var totalData = headers.Sum(h => h.Header.DataBytes);

        using var outFs = File.Create(output);
        using var bw = new BinaryWriter(outFs, Encoding.ASCII, leaveOpen: false);
        WriteHeader(bw, fmt, (uint)totalData);

        var buf = new byte[64 * 1024];
        foreach (var (path, (_, dataBytes)) in headers)
        {
            CopyDataChunk(path, outFs, buf, dataBytes);
        }

        return totalData;
    }

    private static void Expect(BinaryReader br, string fourCc)
    {
        var actual = Encoding.ASCII.GetString(br.ReadBytes(4));
        if (actual != fourCc)
            throw new InvalidDataException(
                $"WAV: expected '{fourCc}' magic, got '{actual}'.");
    }

    private static void WriteHeader(BinaryWriter bw, WavFormat fmt, uint dataBytes)
    {
        bw.Write(Encoding.ASCII.GetBytes("RIFF"));
        bw.Write(36u + dataBytes);              // chunk size = 4 + (8 + 16) + (8 + dataBytes)
        bw.Write(Encoding.ASCII.GetBytes("WAVE"));

        bw.Write(Encoding.ASCII.GetBytes("fmt "));
        bw.Write(16u);                          // PCM subchunk size
        bw.Write((ushort)1);                    // audio format = PCM
        bw.Write(fmt.NumChannels);
        bw.Write(fmt.SampleRate);
        bw.Write(fmt.ByteRate);
        bw.Write(fmt.BlockAlign);
        bw.Write(fmt.BitsPerSample);

        bw.Write(Encoding.ASCII.GetBytes("data"));
        bw.Write(dataBytes);
    }

    private static void CopyDataChunk(string path, Stream output, byte[] buf, long dataBytes)
    {
        using var fs = File.OpenRead(path);
        using var br = new BinaryReader(fs, Encoding.ASCII, leaveOpen: false);

        // Re-walk to the data chunk — cheaper than threading the file
        // position out of ReadHeader and re-opening anyway.
        Expect(br, "RIFF");
        _ = br.ReadUInt32();
        Expect(br, "WAVE");
        while (true)
        {
            var chunkId = Encoding.ASCII.GetString(br.ReadBytes(4));
            var chunkSize = br.ReadUInt32();
            if (chunkId == "data") break;
            var skip = chunkSize + (chunkSize & 1);
            fs.Seek(skip, SeekOrigin.Current);
        }

        var remaining = dataBytes;
        while (remaining > 0)
        {
            var want = (int)Math.Min(buf.Length, remaining);
            var got = fs.Read(buf, 0, want);
            if (got == 0)
                throw new EndOfStreamException(
                    $"WAV {path}: data subchunk shorter than its declared length.");
            output.Write(buf, 0, got);
            remaining -= got;
        }
    }
}
