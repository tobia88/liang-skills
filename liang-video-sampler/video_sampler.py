#!/usr/bin/env python3
"""Extract timestamped screenshots from a local video/GIF for agent review."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable


AUDIO_SIZE_WARNING_BYTES = 25 * 1024 * 1024


def parse_time(value: str) -> float:
    """Parse seconds or HH:MM:SS[.mmm] into seconds."""
    text = str(value).strip()
    if not text:
        raise argparse.ArgumentTypeError("time value cannot be empty")

    if ":" not in text:
        try:
            seconds = float(text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid time value: {value}") from exc
        if seconds < 0:
            raise argparse.ArgumentTypeError("time value must be non-negative")
        return seconds

    parts = text.split(":")
    if len(parts) > 3:
        raise argparse.ArgumentTypeError(f"invalid time value: {value}")

    try:
        numbers = [float(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid time value: {value}") from exc

    while len(numbers) < 3:
        numbers.insert(0, 0.0)

    hours, minutes, seconds = numbers
    total = hours * 3600 + minutes * 60 + seconds
    if total < 0:
        raise argparse.ArgumentTypeError("time value must be non-negative")
    return total


def format_time(seconds: float) -> str:
    millis = int(round((seconds - math.floor(seconds)) * 1000))
    whole = int(math.floor(seconds))
    if millis >= 1000:
        whole += 1
        millis -= 1000
    hours = whole // 3600
    minutes = (whole % 3600) // 60
    secs = whole % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def safe_time_for_filename(seconds: float) -> str:
    return format_time(seconds).replace(":", "-")


def sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
    return cleaned or "video"


def candidate_executable_paths(name: str) -> Iterable[Path]:
    executable = f"{name}.exe" if os.name == "nt" else name

    exact_env = os.environ.get(f"{name.upper()}_PATH")
    if exact_env:
        yield Path(exact_env)

    ffmpeg_dir = os.environ.get("FFMPEG_DIR")
    if ffmpeg_dir:
        yield Path(ffmpeg_dir) / executable

    if os.name != "nt":
        return

    program_roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
    ]
    for root in [Path(value) for value in program_roots if value]:
        yield root / "Krita (x64)" / "bin" / executable
        yield root / "SteelSeries" / "GG" / "apps" / "moments" / executable
        yield root / "EaseUS" / "EaseUS Data Recovery Wizard" / "VideoViewer" / executable

    chocolatey_root = Path(os.environ.get("ChocolateyInstall", r"C:\ProgramData\chocolatey"))
    yield chocolatey_root / "bin" / executable
    yield Path.home() / "scoop" / "shims" / executable


def find_executable(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path

    for candidate in candidate_executable_paths(name):
        if candidate.is_file():
            return str(candidate)

    raise SystemExit(
        f"Error: {name} not found. Install FFmpeg or set FFMPEG_DIR/{name.upper()}_PATH.\n"
        "Windows: winget install Gyan.FFmpeg  OR  scoop install ffmpeg  OR  choco install ffmpeg\n"
        "macOS: brew install ffmpeg\n"
        "Ubuntu/Debian: sudo apt-get install ffmpeg"
    )


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def probe_duration(ffprobe: str, input_path: Path) -> float | None:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    try:
        duration = float(text)
    except ValueError:
        return None
    if not math.isfinite(duration) or duration <= 0:
        return None
    return duration


def build_timestamps(start: float, end: float, interval: float, max_frames: int) -> list[float]:
    if interval <= 0:
        raise SystemExit("Error: --interval must be greater than 0")
    if max_frames <= 0:
        raise SystemExit("Error: --max-frames must be greater than 0")
    if end < start:
        raise SystemExit("Error: --end must be greater than or equal to --start")
    if math.isclose(start, end):
        return [start]

    count_by_interval = int(math.floor((end - start) / interval)) + 1
    interval_times = [start + i * interval for i in range(count_by_interval)]
    if interval_times[-1] < end and len(interval_times) < max_frames:
        interval_times.append(end)

    if len(interval_times) <= max_frames:
        return interval_times

    if max_frames == 1:
        return [start]

    step = (end - start) / (max_frames - 1)
    return [start + i * step for i in range(max_frames)]


def escape_drawtext_text(text: str) -> str:
    # Escape characters meaningful to ffmpeg filter parser.
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def frame_filter(timestamp: str, width: int, overlay: bool) -> str | None:
    filters: list[str] = []
    if width > 0:
        filters.append(f"scale={width}:-2")
    if overlay:
        label = escape_drawtext_text(timestamp)
        filters.append(
            "drawtext="
            f"text='{label}':"
            "x=12:y=12:fontsize=28:fontcolor=white:"
            "box=1:boxcolor=black@0.65:boxborderw=8"
        )
    return ",".join(filters) if filters else None


def extract_one_frame(
    ffmpeg: str,
    input_path: Path,
    output_path: Path,
    timestamp_seconds: float,
    width: int,
    overlay: bool,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{timestamp_seconds:.3f}",
        "-i",
        str(input_path),
        "-frames:v",
        "1",
    ]
    vf = frame_filter(format_time(timestamp_seconds), width, overlay)
    if vf:
        cmd.extend(["-vf", vf])
    cmd.append(str(output_path))
    return run_command(cmd)


def extract_frames(
    ffmpeg: str,
    input_path: Path,
    out_dir: Path,
    timestamps: Iterable[float],
    width: int,
    overlay: bool,
) -> tuple[list[dict], bool]:
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames: list[dict] = []
    overlay_used = overlay
    overlay_failed = False

    for index, timestamp in enumerate(timestamps, start=1):
        time_label = format_time(timestamp)
        filename = f"frame_{index:04d}_t{safe_time_for_filename(timestamp)}.jpg"
        output_path = frames_dir / filename

        result = extract_one_frame(ffmpeg, input_path, output_path, timestamp, width, overlay_used)
        if result.returncode != 0 and overlay_used:
            overlay_failed = True
            overlay_used = False
            result = extract_one_frame(ffmpeg, input_path, output_path, timestamp, width, False)

        if result.returncode != 0:
            print(
                f"Warning: failed to extract frame at {time_label}: {result.stderr.strip()}",
                file=sys.stderr,
            )
            continue

        frames.append(
            {
                "index": index,
                "timestamp_seconds": round(timestamp, 3),
                "timestamp": time_label,
                "file": str(output_path),
            }
        )

    if overlay_failed:
        print(
            "Warning: timestamp overlay failed, likely because FFmpeg drawtext is unavailable. "
            "Generated timestamped filenames instead.",
            file=sys.stderr,
        )

    return frames, overlay_used


def extract_audio(ffmpeg: str, input_path: Path, out_dir: Path) -> Path | None:
    audio_path = out_dir / "audio.mp3"
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "48k",
        str(audio_path),
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        print(
            f"Warning: audio extraction failed or input has no audio: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return None
    return audio_path


def write_manifests(
    out_dir: Path,
    input_path: Path,
    duration: float,
    args: argparse.Namespace,
    frames: list[dict],
    overlay_used: bool,
    audio_path: Path | None,
) -> tuple[Path, Path]:
    manifest = {
        "input": str(input_path),
        "output_dir": str(out_dir),
        "duration_seconds": round(duration, 3),
        "duration": format_time(duration),
        "start_seconds": round(args.start, 3),
        "end_seconds": round(args.end, 3),
        "interval_seconds": args.interval,
        "max_frames": args.max_frames,
        "width": args.width,
        "timestamp_overlay": overlay_used,
        "audio": str(audio_path) if audio_path else None,
        "frames": frames,
    }

    json_path = out_dir / "manifest.json"
    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    md_path = out_dir / "manifest.md"
    lines = [
        "# Video Sample Manifest",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{out_dir}`",
        f"- Duration: `{format_time(duration)}` ({duration:.3f}s)",
        f"- Sample window: `{format_time(args.start)}` → `{format_time(args.end)}`",
        f"- Interval: `{args.interval}` seconds",
        f"- Frames extracted: `{len(frames)}`",
        f"- Timestamp overlay: `{'yes' if overlay_used else 'no'}`",
    ]
    if audio_path:
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        lines.append(f"- Audio: `{audio_path}` ({size_mb:.2f} MB)")
        if audio_path.stat().st_size > AUDIO_SIZE_WARNING_BYTES:
            lines.append("- Audio warning: file is larger than 25 MB; split/compress before Groq Whisper transcription.")
    lines.extend(["", "## Frames", "", "| # | Timestamp | File |", "|---:|-----------|------|"])
    for frame in frames:
        lines.append(f"| {frame['index']} | {frame['timestamp']} | `{frame['file']}` |")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, json_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract timestamped screenshots from a local video/GIF for agent review."
    )
    parser.add_argument("input", type=Path, help="Input video/GIF path")
    parser.add_argument("--output", "-o", type=Path, help="Output directory")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between samples (default: 2)")
    parser.add_argument("--max-frames", type=int, default=60, help="Maximum frames to extract (default: 60)")
    parser.add_argument("--start", type=parse_time, default=0.0, help="Start time in seconds or HH:MM:SS[.mmm]")
    parser.add_argument("--end", type=parse_time, help="End time in seconds or HH:MM:SS[.mmm]")
    parser.add_argument("--duration", type=parse_time, help="Manual duration override if ffprobe cannot read it")
    parser.add_argument("--width", type=int, default=960, help="Output width in pixels; 0 keeps original size (default: 960)")
    parser.add_argument("--no-overlay", action="store_true", help="Do not burn timestamps into images")
    parser.add_argument("--audio", action="store_true", help="Extract compressed mono audio.mp3 for optional transcription")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    input_path = args.input.expanduser().resolve()
    if not input_path.exists() or not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1
    if args.width < 0:
        print("Error: --width must be 0 or greater", file=sys.stderr)
        return 1

    ffmpeg = find_executable("ffmpeg")
    ffprobe = find_executable("ffprobe")

    duration = args.duration if args.duration is not None else probe_duration(ffprobe, input_path)
    if duration is None:
        print(
            "Error: could not determine video duration with ffprobe. "
            "Pass --duration seconds or HH:MM:SS as an override.",
            file=sys.stderr,
        )
        return 1

    args.end = args.end if args.end is not None else duration
    if args.start > duration:
        print("Error: --start is beyond video duration", file=sys.stderr)
        return 1
    args.end = min(args.end, duration)
    if args.end > args.start and math.isclose(args.end, duration):
        args.end = max(args.start, duration - 0.001)

    timestamps = build_timestamps(args.start, args.end, args.interval, args.max_frames)

    if args.output:
        out_dir = args.output.expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = Path(tempfile.gettempdir()) / "liang-video-sampler" / f"{sanitize_name(input_path.stem)}-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    frames, overlay_used = extract_frames(
        ffmpeg=ffmpeg,
        input_path=input_path,
        out_dir=out_dir,
        timestamps=timestamps,
        width=args.width,
        overlay=not args.no_overlay,
    )

    if not frames:
        print("Error: no frames were extracted", file=sys.stderr)
        return 1

    audio_path = extract_audio(ffmpeg, input_path, out_dir) if args.audio else None
    md_path, json_path = write_manifests(out_dir, input_path, duration, args, frames, overlay_used, audio_path)

    print(f"OUTPUT_DIR={out_dir}")
    print(f"MANIFEST_MD={md_path}")
    print(f"MANIFEST_JSON={json_path}")
    print(f"FRAMES_DIR={out_dir / 'frames'}")
    if audio_path:
        print(f"AUDIO={audio_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
