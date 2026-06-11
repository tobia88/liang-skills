---
name: liang-video-sampler
description: Extract timestamped screenshots from local video files and GIFs so the agent can visually understand and summarize gameplay clips, UI recordings, animations, trailers, or other local videos. Use when the user provides an mp4, mov, webm, mkv, avi, or gif and asks for visual analysis, video understanding, frame summaries, or "watch this video" on a local file.
---

# Liang Video Sampler

Turn a local video/GIF into timestamped screenshots plus a manifest the agent can inspect.

## What This Skill Does

- Samples frames from local videos: `mp4`, `mov`, `webm`, `mkv`, `avi`, `gif`, and most FFmpeg-readable formats.
- Writes timestamped image files, e.g. `frame_0001_t00-00-04.000.jpg`.
- Optionally burns the timestamp onto each frame.
- Writes `manifest.md` and `manifest.json` for fast review.
- Optionally extracts a compressed audio file that can be sent through the `transcribe` skill.

## Setup

Requires Python 3 and FFmpeg/FFprobe. The script first checks `PATH`, then `FFMPEG_DIR`, `FFMPEG_PATH`, `FFPROBE_PATH`, and a few common Windows app-bundled locations such as Krita.

Check:

```bash
python --version
ffmpeg -version
ffprobe -version
```

Install FFmpeg if missing:

```bash
# Windows, choose one
winget install Gyan.FFmpeg
scoop install ffmpeg
choco install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Usage

```bash
python {baseDir}/video_sampler.py "path/to/video.mp4"
```

Recommended agent workflow for visual understanding:

```bash
python {baseDir}/video_sampler.py "path/to/video.mp4" --interval 2 --max-frames 40 --width 960 --audio
```

For GIFs or short UI recordings:

```bash
python {baseDir}/video_sampler.py "path/to/clip.gif" --interval 0.5 --max-frames 60 --width 960
```

For long videos, do a coarse pass first:

```bash
python {baseDir}/video_sampler.py "path/to/video.mp4" --interval 10 --max-frames 60 --width 960
```

Then resample interesting sections:

```bash
python {baseDir}/video_sampler.py "path/to/video.mp4" --start 00:02:10 --end 00:02:40 --interval 1 --width 1280
```

## Options

```text
--output, -o <dir>       Output directory. Default: system temp/liang-video-sampler/<video>-<timestamp>
--interval <seconds>     Desired seconds between samples. Default: 2
--max-frames <count>     Cap frame count. If interval would exceed this, samples are spread evenly. Default: 60
--start <time>           Start time as seconds or HH:MM:SS[.mmm]. Default: 0
--end <time>             End time as seconds or HH:MM:SS[.mmm]. Default: video duration
--duration <time>        Manual duration override if ffprobe cannot read duration
--width <pixels>         Output width; keeps aspect ratio. Use 0 for original size. Default: 960
--no-overlay             Do not burn timestamp text into images; filenames still contain timestamps
--audio                  Extract compressed mono audio as audio.mp3 for optional transcription
```

## Agent Review Procedure

1. Run `video_sampler.py` on the local video/GIF.
2. Read the generated `manifest.md` first.
3. Inspect a representative subset of frames with the `read` tool. Do not load hundreds of frames blindly; use the manifest timestamps.
4. If audio matters and `audio.mp3` was generated, invoke/use the `transcribe` skill if `GROQ_API_KEY` is available.
5. Summarize using both the frame sequence and transcript when available.
6. For ambiguous or fast-moving moments, resample a narrower time range at a smaller interval.

## Output

The script prints paths like:

```text
OUTPUT_DIR=C:/Users/Liang/AppData/Local/Temp/liang-video-sampler/demo-20260607-120000
MANIFEST_MD=.../manifest.md
MANIFEST_JSON=.../manifest.json
AUDIO=.../audio.mp3
```

`manifest.md` contains a timestamp/file table for quick human and agent review.

## Notes

- This skill does not upload videos anywhere; it uses local FFmpeg.
- Frame extraction works without Groq/API keys.
- If FFmpeg is installed but not on `PATH`, set `FFMPEG_DIR` to the folder containing `ffmpeg.exe` and `ffprobe.exe`.
- Audio transcription is separate and optional via the `transcribe` skill.
- If FFmpeg lacks the `drawtext` filter, the script automatically falls back to timestamped filenames without burned-in overlay.
