"""
image_analyzer.py
------------------
Standalone image metadata analyzer.

Usage:
    python image_analyzer.py path/to/image.jpg

Prints a metadata report:
    File Name, File Size, File Format, Width, Height, Resolution,
    Color Mode, and EXIF metadata (Camera, Date Taken, Orientation, ...)

Minimum supported formats: JPG/JPEG, PNG
Bonus supported formats:   TIFF, WEBP, BMP

Requires: Pillow  ->  pip install pillow
"""

import argparse
import os
import sys

from PIL import Image
from PIL.ExifTags import TAGS

LABEL_WIDTH = 16

# EXIF orientation tag values -> human readable description
ORIENTATION_MAP = {
    1: "Normal",
    2: "Mirrored horizontal",
    3: "Rotated 180",
    4: "Mirrored vertical",
    5: "Mirrored horizontal, rotated 270 CW",
    6: "Rotated 90 CW",
    7: "Mirrored horizontal, rotated 90 CW",
    8: "Rotated 270 CW",
}


def format_size(size_bytes: int) -> str:
    """Convert a byte count into a human-readable string (B/KB/MB/GB)."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def line(label: str, value) -> str:
    """Format one 'Label   : value' line with aligned colons."""
    if value in (None, "", {}):
        value = "Not available"
    return f"{label:<{LABEL_WIDTH}}: {value}"


def extract_exif(img: Image.Image) -> dict:
    """Pull all readable EXIF tags into a plain dict of {tag_name: value}."""
    exif_data = {}
    try:
        exif = img.getexif()
        if not exif:
            return exif_data
        for tag_id, value in exif.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            if isinstance(value, bytes):
                try:
                    value = value.decode(errors="replace")
                except Exception:
                    value = str(value)
            exif_data[tag_name] = value
    except Exception:
        pass
    return exif_data


def analyze_image(file_path: str) -> str:
    """Analyze an image file and return the formatted metadata report text."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = format_size(os.path.getsize(file_path))
    file_name = os.path.basename(file_path)

    with Image.open(file_path) as img:
        width, height = img.size
        raw_exif = extract_exif(img)

        camera_parts = [str(raw_exif[k]) for k in ("Make", "Model") if k in raw_exif]
        camera = " ".join(camera_parts) if camera_parts else "Not available"

        date_taken = (
            raw_exif.get("DateTimeOriginal") or raw_exif.get("DateTime") or "Not available"
        )

        orientation_raw = raw_exif.get("Orientation")
        orientation = (
            ORIENTATION_MAP.get(orientation_raw, f"Unknown ({orientation_raw})")
            if orientation_raw is not None
            else "Not available"
        )

        lines = [
            "=" * 32,
            "IMAGE METADATA REPORT",
            "=" * 32,
            line("File Name", file_name),
            line("File Size", file_size),
            line("File Format", img.format),
            line("Width", width),
            line("Height", height),
            line("Resolution", f"{width} x {height}"),
            line("Color Mode", img.mode),
            "",
            "EXIF Metadata",
            "-" * 32,
            line("Camera", camera),
            line("Date Taken", date_taken),
            line("Orientation", orientation),
        ]

        extra_tags = {
            k: v for k, v in raw_exif.items()
            if k not in ("Make", "Model", "DateTime", "DateTimeOriginal", "Orientation")
        }
        if extra_tags:
            lines.append("")
            lines.append("Other EXIF Tags")
            lines.append("-" * 32)
            for k, v in extra_tags.items():
                lines.append(line(k, v))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze an image file and print its metadata.")
    parser.add_argument("file", help="Path to the image file (.jpg, .jpeg, .png, .tiff, .webp, .bmp)")
    args = parser.parse_args()

    try:
        report = analyze_image(args.file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(report)


if __name__ == "__main__":
    main()