"""
audio_analyzer.py
------------------
Standalone audio metadata analyzer.

Usage:
    python audio_analyzer.py path/to/song.mp3

Prints a metadata report:
    File Name, File Size, Container, Duration,
    AUDIO (Codec, Channels, Sampling Rate, Bit Rate),
    METADATA (any embedded tags: title, artist, album, ...)

Supported formats: MP3, WAV, FLAC, OGG, M4A, AAC (anything ffprobe reads)

Requires: ffmpeg/ffprobe installed and on PATH
    Windows: https://ffmpeg.org/download.html
    Mac:     brew install ffmpeg
    Linux:   sudo apt install ffmpeg
"""

import argparse
import json
import os
import subprocess
import sys

LABEL_WIDTH = 16


def format_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def line(label: str, value) -> str:
    if value in (None, "", {}):
        value = "Not available"
    return f"{label:<{LABEL_WIDTH}}: {value}"


def format_duration(seconds_str) -> str:
    try:
        total = float(seconds_str)
    except (TypeError, ValueError):
        return "Not available"
    h = int(total // 3600)
    m = int((total % 3600) // 60)
    s = int(total % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_bitrate(bitrate_str) -> str:
    try:
        bits = int(bitrate_str)
        return f"{bits / 1000:.0f} kb/s"
    except (TypeError, ValueError):
        return "Not available"


def run_ffprobe(file_path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe not found. Please install ffmpeg "
            "(https://ffmpeg.org/download.html) and ensure it's on your PATH."
        )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed to read file: {result.stderr.strip()}")
    return json.loads(result.stdout)


def analyze_audio(file_path: str) -> str:
    """Analyze an audio file and return the formatted metadata report text."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = format_size(os.path.getsize(file_path))
    file_name = os.path.basename(file_path)

    probe = run_ffprobe(file_path)
    fmt = probe.get("format", {})
    streams = probe.get("streams", [])
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    channels = audio_stream.get("channels")
    channel_layout = audio_stream.get("channel_layout")
    channels_display = (
        f"{channels} ({channel_layout})" if channels and channel_layout else channels
    )

    lines = [
        "=" * 32,
        "AUDIO METADATA REPORT",
        "=" * 32,
        line("File Name", file_name),
        line("File Size", file_size),
        line("Container", fmt.get("format_long_name", fmt.get("format_name"))),
        line("Duration", format_duration(fmt.get("duration"))),
        "",
        "AUDIO",
        "-" * 32,
        line("Codec", audio_stream.get("codec_long_name", audio_stream.get("codec_name"))),
        line("Channels", channels_display),
        line(
            "Sampling Rate",
            f"{audio_stream.get('sample_rate')} Hz" if audio_stream.get("sample_rate") else None,
        ),
        line("Bit Rate", format_bitrate(audio_stream.get("bit_rate") or fmt.get("bit_rate"))),
    ]

    tags = fmt.get("tags", {}) or {}
    if tags:
        lines.append("")
        lines.append("METADATA")
        lines.append("-" * 32)
        for k, v in tags.items():
            lines.append(line(k.title(), v))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze an audio file and print its metadata.")
    parser.add_argument("file", help="Path to the audio file (.mp3, .wav, .flac, .ogg, .m4a, .aac)")
    args = parser.parse_args()

    try:
        report = analyze_audio(args.file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(report)


if __name__ == "__main__":
    main()