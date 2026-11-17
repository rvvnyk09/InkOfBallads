"""b2s-video command line."""
from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

from . import __version__
from .render import SIZES, Job, Progress, RenderError, default_workers
from .song import LOOKS, SongError, build_pages, default_look, load_song, song_title, source_field, unknown_tags, \
    parse_sections, lyric_entries
from .timing import TimingError, format_timestamp, line_times, load_turns_file, parse_inline, timing_template, \
    validate_turns

COMMANDS = ("render", "init-timing", "contact-sheet", "preview", "suggest-timing", "upload-text")


def _err(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def _warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


# ---------------------------------------------------------------- shared options

def _add_song(p, audio=True):
    p.add_argument("--song", required=True, help="b2s song JSON file")
    p.add_argument("--version", help="for a song file with several versions: its number, channel or title "
                                     "(default: the one whose title matches the audio file name)")
    if audio:
        p.add_argument("--audio", required=True, help="MP3 (or any audio ffmpeg reads)")


def _add_pages(p):
    p.add_argument("--no-cover", action="store_true", help="leave out the cover page")
    p.add_argument("--no-back-cover", action="store_true", help="leave out the back cover page")


def _add_turns(p):
    p.add_argument("--turns", help='timestamps inline, for example "0:03,0:10,0:17"')
    p.add_argument("--turns-file", help="timestamps file: .txt (one per line, # comments) or .json {\"turns\": [...]}")


def _add_look(p):
    p.add_argument("--format", choices=SIZES, default="16x9", help="16x9 = 1920x1080 (YouTube), 9x16 = 1080x1920 (Shorts, Reels, TikTok)")
    p.add_argument("--look", choices=LOOKS,
                   help="notebook = purple spiral notebook in Caveat handwriting (default); "
                        "kids = storybook in rounded Fredoka; classic = storybook in serif Lora")
    p.add_argument("--channel", help="text on the back cover, for example your channel name")
    p.add_argument("--logo", help="logo for the notebook: on the cover (in place of the channel line), as a faint "
                                  "watermark behind the lyrics, and on The End page. A PNG with a transparent "
                                  "background is best (.png .webp .svg .jpg)")
    p.add_argument("--logo-mark", help="small symbol for the purple page tabs, in place of the note "
                                       "(transparent PNG; drawn in white)")
    p.add_argument("--subscribe", action=argparse.BooleanOptionalAction, default=True,
                   help="write \"Like & Subscribe\" on The End page, with \"Subscribe\" circled by hand "
                        "(notebook look; on by default, --no-subscribe leaves it out)")
    p.add_argument("--highlight", action="store_true",
                   help="mark the line being sung (highlighter in the notebook, berry red in the storybook); "
                        "off by default; needs --line-timing even or per-line times")
    p.add_argument("--line-timing", choices=["all", "even"], default="all",
                   help="all = every line of a page shown at once, with no running highlight (default); "
                        "even = lines light up one by one across the page")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="b2s-video", description="Turn a b2s song JSON and an MP3 into a page-turn lyric video.",
                                 epilog="render is the default command, so `b2s-video --song ...` renders.")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="command", metavar="COMMAND")

    r = sub.add_parser("render", help="render the MP4 (or one still with --still)")
    _add_song(r)
    r.add_argument("--out", required=True, help="output .mp4, or .png with --still")
    _add_turns(r)
    _add_look(r)
    _add_pages(r)
    r.add_argument("--fps", type=int, default=30, help="frames per second (default 30)")
    r.add_argument("--workers", type=int, default=None,
                   help=f"browser processes rendering in parallel (default {default_workers()} on this machine)")
    r.add_argument("--crf", type=int, default=20, help="x264 quality, lower is better (default 20)")
    r.add_argument("--still", type=float, metavar="SECONDS", help="save one PNG frame at this time instead of a video")
    r.add_argument("--max-seconds", type=float, help="render only the first N seconds (test renders)")

    i = sub.add_parser("init-timing", help="write a timestamps file to fill in, one line per page")
    _add_song(i, audio=False)
    i.add_argument("--out", required=True, help="file to write, for example turns.txt")
    i.add_argument("--force", action="store_true", help="overwrite the file if it exists")
    _add_pages(i)

    c = sub.add_parser("contact-sheet", help="a grid of stills, one per page, to check timestamps")
    _add_song(c)
    c.add_argument("--out", required=True, help="output PNG")
    _add_turns(c)
    _add_look(c)
    _add_pages(c)

    v = sub.add_parser("preview", help="an HTML page that plays the song in its template in your browser")
    _add_song(v)
    v.add_argument("--out", required=True, help="output .html (keep it where it can still find the audio)")
    _add_turns(v)
    _add_look(v)
    _add_pages(v)

    s = sub.add_parser("suggest-timing", help="suggest timestamps with local forced alignment (optional extra)")
    _add_song(s)
    s.add_argument("--out", required=True, help="timestamps file to write")
    s.add_argument("--separate-vocals", action="store_true", help="isolate vocals with Demucs first")
    s.add_argument("--model", default="base", help="Whisper model for stable-ts (default base)")
    s.add_argument("--language", default="en")
    s.add_argument("--force", action="store_true", help="overwrite the file if it exists")
    _add_pages(s)

    u = sub.add_parser("upload-text", help="the song JSON's youtube block as a plain text file to copy and paste")
    u.add_argument("--song", required=True, help="b2s song JSON file with a \"youtube\" block")
    u.add_argument("--version", help="for a song file with several versions: its number, channel or title "
                                     "(default: the one version that has a youtube block)")
    u.add_argument("--out", help="text file to write (default: <song folder>/out/<folder>-youtube.txt)")
    u.add_argument("--force", action="store_true", help="replace an existing file that upload-text did not write")
    return ap


# ---------------------------------------------------------------- helpers

def _pages(args):
    song = load_song(args.song, args.version, getattr(args, "audio", None))
    print(f"Song: {song_title(song)}", file=sys.stderr)
    pages = build_pages(song, cover=not args.no_cover, back=not args.no_back_cover)
    unknown = unknown_tags(parse_sections(lyric_entries(song)))
    if unknown:
        print("note: tags not in the usual list (shown as written): " + ", ".join(f"[{t}]" for t in unknown),
              file=sys.stderr)
    return song, pages


def _flags(args) -> str:
    return " ".join(f for f, on in (("--no-cover", args.no_cover), ("--no-back-cover", args.no_back_cover)) if on)


def _turn_values(args):
    if args.turns and args.turns_file:
        raise TimingError("Give timestamps with --turns or --turns-file, not both.")
    if args.turns:
        return parse_inline(args.turns), None
    if args.turns_file:
        return load_turns_file(args.turns_file)
    raise TimingError("No timestamps given. Use --turns \"0:03,0:10,...\" or --turns-file turns.txt.\n"
                      f"Make a file to fill in with: b2s-video init-timing --song {args.song} --out turns.txt")


def _job(args, song, pages, audio_seconds) -> Job:
    values, custom = _turn_values(args)
    starts, warnings = validate_turns(pages, values, audio_seconds)
    for w in warnings:
        _warn(w)
    lines = line_times(pages, starts, audio_seconds, args.line_timing, custom)
    return Job(pages=pages, starts=starts, lines=lines, format=args.format, look=args.look or default_look(song),
               title=song_title(song), work=source_field(song, "work"), author=source_field(song, "author"),
               channel=args.channel, logo=_image(args, "logo"), mark=_image(args, "logo_mark"),
               highlight=args.highlight, subscribe=args.subscribe, total=audio_seconds)


LOGO_TYPES = {".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def _image(args, name: str) -> str | None:
    """--logo / --logo-mark as a data: URI."""
    value, flag = getattr(args, name), "--" + name.replace("_", "-")
    if not value:
        return None
    path = Path(value)
    kind = LOGO_TYPES.get(path.suffix.lower())
    if kind is None:
        raise SongError(f"{flag} {path}: use a {', '.join(LOGO_TYPES)} image.")
    if not path.is_file():
        raise SongError(f"{flag} {path}: file not found.")
    if kind == "image/jpeg":
        _warn(f"{flag} {path.name} is a JPG, which cannot be transparent: its background (even a checkerboard) "
              f"shows on the cover, and inside the book the whole picture becomes a solid block. "
              f"A PNG with a transparent background looks right.")
    if (args.look or "notebook") != "notebook":
        _warn(f"{flag} is drawn in the notebook look only; the storybook looks ignore it.")
    return f"data:{kind};base64," + base64.b64encode(path.read_bytes()).decode()


def _report_layout(info, pages):
    for n in info.overflow:
        _warn(f"page {n} ({pages[n - 1].label}) has too much text to fit even at the smallest size; "
              f"some of it may be clipped. Consider splitting the section.")


def _check_out(path: str, suffixes: tuple[str, ...]):
    out = Path(path)
    if out.suffix.lower() not in suffixes:
        raise SongError(f"--out {path}: expected a {' or '.join(suffixes)} file.")
    if not out.parent.exists():
        raise SongError(f"--out {path}: the folder {out.parent} does not exist.")
    return out


# ---------------------------------------------------------------- commands

def cmd_render(args) -> int:
    from .render import probe_duration, render_still, render_video
    song, pages = _pages(args)
    audio_seconds = probe_duration(args.audio)
    job = _job(args, song, pages, audio_seconds)
    if args.still is not None:
        out = _check_out(args.out, (".png",))
        if not 0 <= args.still <= audio_seconds:
            raise TimingError(f"--still {args.still} is outside the audio (0 to {audio_seconds:.1f} s).")
        info = render_still(job, args.still, out)
        _report_layout(info, pages)
        print(f"Saved {out} (frame at {format_timestamp(args.still)})")
        return 0
    out = _check_out(args.out, (".mp4",))
    if args.fps < 1 or args.fps > 120:
        raise TimingError("--fps must be between 1 and 120.")
    duration = audio_seconds
    if args.max_seconds is not None:
        if args.max_seconds <= 0:
            raise TimingError("--max-seconds must be more than 0.")
        duration = min(audio_seconds, args.max_seconds)
    workers = args.workers or default_workers()
    print(f"Rendering {len(pages)} pages, {format_timestamp(duration)} at {args.fps} fps, {args.format}, "
          f"{job.look} look, {workers} worker{'s' if workers != 1 else ''} -> {out}", file=sys.stderr)
    info = render_video(job, args.audio, out, fps=args.fps, duration=duration, workers=workers, crf=args.crf,
                        progress=Progress())
    _report_layout(info, pages)
    print(f"Saved {out}")
    return 0


def cmd_init_timing(args) -> int:
    song, pages = _pages(args)
    out = Path(args.out)
    if out.exists() and not args.force:
        raise SongError(f"{out} already exists. Use --force to overwrite it.")
    out.write_text(timing_template(pages, song_title(song), _flags(args)) + "\n", encoding="utf-8")
    print(f"Wrote {out}: {len(pages) - 1} timestamps to fill in for {len(pages)} pages.")
    return 0


def cmd_contact_sheet(args) -> int:
    from .contact import contact_sheet
    from .render import probe_duration
    song, pages = _pages(args)
    out = _check_out(args.out, (".png",))
    job = _job(args, song, pages, probe_duration(args.audio))
    times, info = contact_sheet(job, out)
    _report_layout(info, pages)
    print(f"Saved {out}: {len(pages)} pages, each shown about 1 s after it starts.")
    return 0


def cmd_preview(args) -> int:
    from .preview import write_preview
    from .render import probe_duration
    song, pages = _pages(args)
    out = _check_out(args.out, (".html",))
    job = _job(args, song, pages, probe_duration(args.audio))
    write_preview(job, args.audio, out)
    print(f"Saved {out}: open it in a browser and press Play (or the space bar).")
    return 0


def cmd_suggest_timing(args) -> int:
    from .render import probe_duration
    from .suggest import align_words, confidence_note, describe, suggest_turns, suggestion_header
    song, pages = _pages(args)
    out = Path(args.out)
    if out.exists() and not args.force:
        raise SongError(f"{out} already exists. Use --force to overwrite it (your own timestamps would be lost).")
    duration = probe_duration(args.audio)
    words = align_words(Path(args.audio), pages, args.model, args.language, args.separate_vocals)
    turns = suggest_turns(pages, words, duration)
    note = confidence_note(words)
    text = timing_template(pages, song_title(song), _flags(args), times=turns,
                           header=suggestion_header(args.model, args.separate_vocals, note))
    out.write_text(text + "\n", encoding="utf-8")
    print(describe(pages, turns))
    print(note)
    print(f"Wrote {out}. Check it (contact-sheet) and edit it; render uses exactly what the file says.")
    return 0


def cmd_upload_text(args) -> int:
    from .upload import default_out, keep_filled, pick_version, placeholders, read_json, upload_text, written_by_us
    song_path = Path(args.song)
    version = pick_version(read_json(song_path), args.version)
    out = Path(args.out) if args.out else default_out(song_path)
    text = upload_text(version, song_path.name, song_path.resolve().parent.name)
    kept = []
    if out.exists():
        if written_by_us(out):
            text, kept = keep_filled(out.read_text(encoding="utf-8", errors="replace"), text)
        elif not args.force:
            raise SongError(f"{out} exists and was not written by upload-text. Use --force to replace it.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    if kept:
        print("Kept what you filled in by hand for: " + ", ".join(sorted(set(kept)))
              + " (put it in the song JSON too, so it is there for good)")
    left = placeholders(text)
    if left:
        print("Placeholders still to fill in: " + ", ".join(left))
    return 0


HANDLERS = {"render": cmd_render, "init-timing": cmd_init_timing, "contact-sheet": cmd_contact_sheet,
            "preview": cmd_preview, "suggest-timing": cmd_suggest_timing, "upload-text": cmd_upload_text}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in COMMANDS and argv[0] not in ("-h", "--help", "--version"):
        argv.insert(0, "render")          # render is the default command
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2
    from .suggest import SuggestError
    try:
        return HANDLERS[args.command](args)
    except (SongError, TimingError) as e:
        _err(str(e))
        return 2
    except (RenderError, SuggestError) as e:
        _err(str(e))
        return 1
    except KeyboardInterrupt:
        _err("stopped.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
