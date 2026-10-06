"""
video_analyzer.py
------------------
Standalone video metadata analyzer.

Usage:
    python video_analyzer.py path/to/video.mp4

Prints a metadata report:
    File Name, File Size, Container, Duration,
    VIDEO (Resolution, Frame Rate, Bit Rate, Codec),
    AUDIO (Codec, Channels, Sampling Rate, Bit Rate),
    METADATA (any embedded tags)

Supported formats: MP4, AVI, MOV, MKV, WEBM (anything ffprobe reads)

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


def format_frame_rate(rate_str) -> str:
    if not rate_str:
        return "Not available"
    try:
        if "/" in rate_str:
            num, denom = rate_str.split("/")
            num, denom = float(num), float(denom)
            fps = num / denom if denom else 0
        else:
            fps = float(rate_str)
        return f"{fps:.2f} fps"
    except (ValueError, ZeroDivisionError):
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


def analyze_video(file_path: str) -> str:
    """Analyze a video file and return the formatted metadata report text."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = format_size(os.path.getsize(file_path))
    file_name = os.path.basename(file_path)

    probe = run_ffprobe(file_path)
    fmt = probe.get("format", {})
    streams = probe.get("streams", [])

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    width = video_stream.get("width")
    height = video_stream.get("height")
    resolution = f"{width}x{height}" if width and height else None

    channels = audio_stream.get("channels")
    channel_layout = audio_stream.get("channel_layout")
    channels_display = (
        f"{channels} ({channel_layout})" if channels and channel_layout else channels
    )

    lines = [
        "=" * 32,
        "VIDEO METADATA REPORT",
        "=" * 32,
        line("File Name", file_name),
        line("File Size", file_size),
        line("Container", fmt.get("format_long_name", fmt.get("format_name"))),
        line("Duration", format_duration(fmt.get("duration"))),
        "",
        "VIDEO",
        "-" * 32,
        line("Resolution", resolution),
        line("Frame Rate", format_frame_rate(video_stream.get("r_frame_rate"))),
        line("Bit Rate", format_bitrate(video_stream.get("bit_rate") or fmt.get("bit_rate"))),
        line("Codec", video_stream.get("codec_long_name", video_stream.get("codec_name"))),
        "",
        "AUDIO",
        "-" * 32,
    ]

    if audio_stream:
        lines.extend([
            line("Codec", audio_stream.get("codec_long_name", audio_stream.get("codec_name"))),
            line("Channels", channels_display),
            line(
                "Sampling Rate",
                f"{audio_stream.get('sample_rate')} Hz" if audio_stream.get("sample_rate") else None,
            ),
            line("Bit Rate", format_bitrate(audio_stream.get("bit_rate"))),
        ])
    else:
        lines.extend([
            line("Codec", "No audio track"),
            line("Channels", "N/A"),
            line("Sampling Rate", "N/A"),
            line("Bit Rate", "N/A"),
        ])

    tags = fmt.get("tags", {}) or {}
    if tags:
        lines.append("")
        lines.append("METADATA")
        lines.append("-" * 32)
        for k, v in tags.items():
            lines.append(line(k.title(), v))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze a video file and print its metadata.")
    parser.add_argument("file", help="Path to the video file (.mp4, .avi, .mov, .mkv, .webm)")
    args = parser.parse_args()

    try:
        report = analyze_video(args.file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(report)


if __name__ == "__main__":
    main()