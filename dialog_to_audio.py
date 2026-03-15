"""
Generate a conversation audio file from a JSON dialog script using Windows SAPI TTS.

Usage:
    python dialog_to_audio.py input/dialog.json [--tag mytag]

Input JSON format (place in input/ folder):
    {
        "lines": [
            {"voice": "Microsoft David Desktop", "text": "Hello, how are you?"},
            {"voice": "Microsoft Zira Desktop", "text": "I'm doing well, thanks!"}
        ],
        "pause_between_ms": 500,
        "rate": 0
    }

Output (written to output/ folder):
    output/<tag>_<datetime>.wav            - Full conversation audio
    output/<tag>_<datetime>_timestamps.json - Timestamps with relative audio path
"""

import sys
import os
import json
import wave
import struct
import tempfile
from datetime import datetime
import win32com.client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


def list_voices():
    """Print all available SAPI voices."""
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    voices = speaker.GetVoices()
    print("Available SAPI voices:")
    for i in range(voices.Count):
        voice = voices.Item(i)
        print(f"  {i}: {voice.GetDescription()}")
    return [voices.Item(i).GetDescription() for i in range(voices.Count)]


def find_voice(speaker, name):
    """Find a voice by partial name match (case-insensitive)."""
    voices = speaker.GetVoices()
    name_lower = name.lower()
    for i in range(voices.Count):
        voice = voices.Item(i)
        if name_lower in voice.GetDescription().lower():
            return voice
    return None


def generate_line_wav(speaker, voice_name, text, rate, filepath):
    """Render a single line of dialog to a WAV file using SAPI."""
    voice = find_voice(speaker, voice_name)
    if voice is None:
        available = list_voices()
        print(f"\nERROR: Voice '{voice_name}' not found.")
        print("Use one of the names listed above (partial match is supported).")
        sys.exit(1)

    speaker.Voice = voice
    speaker.Rate = rate

    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(filepath, 3)  # 3 = SSFMCreateForWrite
    speaker.AudioOutputStream = stream
    speaker.Speak(text)
    stream.Close()


def get_wav_duration_ms(filepath):
    """Get duration of a WAV file in milliseconds."""
    with wave.open(filepath, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return (frames / rate) * 1000


def concatenate_wavs(wav_files, output_path):
    """Concatenate multiple WAV files into one."""
    if not wav_files:
        return
    with wave.open(wav_files[0], "rb") as wf:
        params = wf.getparams()
    with wave.open(output_path, "wb") as out:
        out.setparams(params)
        for fpath in wav_files:
            with wave.open(fpath, "rb") as wf:
                out.writeframes(wf.readframes(wf.getnframes()))


def create_silence_file(duration_ms, reference_wav, output_path):
    """Create a silence WAV file matching the reference WAV's format."""
    with wave.open(reference_wav, "rb") as ref:
        n_channels = ref.getnchannels()
        sample_width = ref.getsampwidth()
        framerate = ref.getframerate()
    num_frames = int(framerate * duration_ms / 1000)
    silence = b"\x00" * (num_frames * n_channels * sample_width)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(framerate)
        wf.writeframes(silence)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate conversation audio from a JSON dialog script using SAPI TTS."
    )
    parser.add_argument("input_json", nargs="?", help="Path to the input dialog JSON file (in input/ folder)")
    parser.add_argument("--tag", default=None, help="Tag for output filenames (default: input filename stem)")
    parser.add_argument("--output-dir", default=None, help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("--list-voices", action="store_true", help="List available SAPI voices and exit")
    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        sys.exit(0)

    if not args.input_json:
        parser.print_help()
        sys.exit(1)

    input_json = args.input_json
    out_dir = args.output_dir or OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    with open(input_json, "r", encoding="utf-8") as f:
        dialog = json.load(f)

    lines = dialog["lines"]
    pause_ms = dialog.get("pause_between_ms", 500)
    rate = dialog.get("rate", 0)

    if not lines:
        print("No dialog lines found.")
        sys.exit(1)

    # Build output filename: <tag>_<YYYYMMDD_HHmmss>
    tag = args.tag or os.path.splitext(os.path.basename(input_json))[0]
    dt_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{tag}_{dt_stamp}"

    wav_filename = f"{base_name}.wav"
    ts_filename = f"{base_name}_timestamps.json"
    output_wav = os.path.join(out_dir, wav_filename)
    output_timestamps = os.path.join(out_dir, ts_filename)

    speaker = win32com.client.Dispatch("SAPI.SpVoice")

    tmp_dir = tempfile.mkdtemp(prefix="dialog_tts_")
    segment_files = []
    timestamps = []
    current_time_ms = 0.0

    print(f"Generating {len(lines)} lines of dialog...")

    for i, line in enumerate(lines):
        voice_name = line["voice"]
        text = line["text"]
        line_path = os.path.join(tmp_dir, f"line_{i:04d}.wav")

        print(f"  [{i+1}/{len(lines)}] {voice_name}: {text[:60]}{'...' if len(text) > 60 else ''}")

        generate_line_wav(speaker, voice_name, text, rate, line_path)
        duration = get_wav_duration_ms(line_path)

        ts_entry = {
            "index": i,
            "voice": voice_name,
            "text": text,
            "start_ms": round(current_time_ms, 1),
            "end_ms": round(current_time_ms + duration, 1),
            "duration_ms": round(duration, 1),
        }
        # Pass through source_paragraphs if present (for podcast-from-paper mapping)
        if "source_paragraphs" in line:
            ts_entry["source_paragraphs"] = line["source_paragraphs"]
        timestamps.append(ts_entry)

        segment_files.append(line_path)
        current_time_ms += duration

        if i < len(lines) - 1 and pause_ms > 0:
            pause_path = os.path.join(tmp_dir, f"pause_{i:04d}.wav")
            create_silence_file(pause_ms, line_path, pause_path)
            segment_files.append(pause_path)
            current_time_ms += pause_ms

    print(f"\nConcatenating into {output_wav}...")
    concatenate_wavs(segment_files, output_wav)

    total_duration = current_time_ms

    # Relative path from timestamps JSON to audio file (same directory)
    audio_relative = wav_filename

    timestamp_output = {
        "source": os.path.abspath(input_json),
        "audio_file": audio_relative,
        "tag": tag,
        "generated": datetime.now().isoformat(),
        "total_duration_ms": round(total_duration, 1),
        "total_duration_formatted": f"{int(total_duration // 60000)}:{int((total_duration % 60000) // 1000):02d}.{int(total_duration % 1000):03d}",
        "lines": timestamps,
    }

    with open(output_timestamps, "w", encoding="utf-8") as f:
        json.dump(timestamp_output, f, indent=2, ensure_ascii=False)

    print(f"Timestamps saved to {output_timestamps}")

    # Cleanup temp files
    for fpath in segment_files:
        try:
            os.unlink(fpath)
        except OSError:
            pass
    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass

    print(f"\nDone! Total duration: {timestamp_output['total_duration_formatted']}")
    print(f"  Audio:      {output_wav}")
    print(f"  Timestamps: {output_timestamps}")


if __name__ == "__main__":
    main()
