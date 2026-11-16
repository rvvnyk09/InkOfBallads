#!/usr/bin/env python3
"""Render a b2s song JSON plus an MP3 into a page-turn lyric video (MP4).

Example:
  python render.py --song hand-in-hand.json --audio Hand_in_Hand.mp3 \
      --turns turns.json --format 16x9 --out hand-in-hand.mp4

See README.md for the turns file and options.
"""
import argparse
import json
import pathlib
import subprocess
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
SIZES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}


def audio_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)], text=True)
    return float(out.strip())


def sections(song):
    """Return the line count of each lyric section (one page each)."""
    counts = []
    for line in song["lyrics"]:
        if line.startswith("["):
            counts.append(0)
        elif line != "" and counts:
            counts[-1] += 1
    return counts


def auto_turns(counts, total, cover=4.0, back=5.0):
    """Placeholder timing: split the song across sections by line count.
    Replace with real times (see README) for a correct sync."""
    body = max(1.0, total - cover - back)
    weight = sum(counts) or 1
    t, out = cover, [cover]
    for c in counts:
        t += body * c / weight
        out.append(round(t, 2))
    return out  # one time per lyric page start, plus the back cover start


def load_turns(arg):
    data = json.loads(pathlib.Path(arg).read_text())
    return data["turns"] if isinstance(data, dict) else data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--song", required=True, help="b2s JSON file")
    ap.add_argument("--audio", required=True, help="MP3 (or other audio) file")
    ap.add_argument("--out", required=True, help="output .mp4 (or .png with --still)")
    ap.add_argument("--turns", help="JSON list of page start times in seconds (see README)")
    ap.add_argument("--format", choices=SIZES, default="16x9")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--look", choices=["kids", "classic"], default="kids")
    ap.add_argument("--channel", default="Your channel name")
    ap.add_argument("--crf", type=int, default=20, help="x264 quality, lower is better")
    ap.add_argument("--max-seconds", type=float, help="render only the first N seconds (for testing)")
    ap.add_argument("--still", type=float, help="save one PNG at this time (seconds) instead of a video")
    args = ap.parse_args()

    song = json.loads(pathlib.Path(args.song).read_text())
    W, H = SIZES[args.format]
    total = audio_duration(args.audio)
    counts = sections(song)
    turns = load_turns(args.turns) if args.turns else auto_turns(counts, total)
    if not args.turns:
        print("No --turns file given: using evenly spaced placeholder times.", file=sys.stderr)
    need = len(counts) + 1
    if len(turns) != need:
        sys.exit(f"Expected {need} turn times (one per lyric section, plus the back cover); got {len(turns)}.")
    if any(b <= a for a, b in zip(turns, turns[1:])):
        sys.exit("Turn times must be increasing.")

    duration = min(total, args.max_seconds) if args.max_seconds else total
    cfg = {"song": song, "turns": turns, "W": W, "H": H, "look": args.look,
           "channel": args.channel, "total": total}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto((HERE / "render_template.html").as_uri())
        page.evaluate("cfg => window.setup(cfg)", cfg)

        if args.still is not None:
            page.evaluate("t => window.renderAt(t)", args.still)
            page.screenshot(path=args.out, type="png")
            browser.close()
            print("Saved", args.out)
            return

        frames = int(duration * args.fps)
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(args.fps), "-i", "-",
             "-i", args.audio, "-map", "0:v", "-map", "1:a", "-t", f"{duration:.3f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
             "-r", str(args.fps), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", args.out],
            stdin=subprocess.PIPE)
        step = max(1, frames // 20)
        try:
            for f in range(frames):
                page.evaluate("t => window.renderAt(t)", f / args.fps)
                ff.stdin.write(page.screenshot(type="jpeg", quality=92))
                if f % step == 0:
                    print(f"  {100 * f // frames}%", file=sys.stderr)
            ff.stdin.close()
        except BrokenPipeError:
            pass
        ff.wait()
        browser.close()
    if ff.returncode != 0:
        sys.exit("ffmpeg failed.")
    print("Saved", args.out)


if __name__ == "__main__":
    main()
