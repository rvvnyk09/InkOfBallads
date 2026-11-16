"""Page-turn timestamps: parsing, files, validation and per-line timing."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from .song import Page

FORMATS_HINT = "use m:ss, mm:ss, mm:ss.s, h:mm:ss or plain seconds (for example 0:03, 1:05.5, 1:02:03, 74.5)"

# Inside a page, lines start 0.4 s after the page and stop 0.8 s before the next page.
LINE_LEAD = 0.4
LINE_TAIL = 0.8
TURN_LEAD = 0.25       # the page turn starts this long before its timestamp (matches template.html)
MIN_SECTION = 2.0      # warn below this many seconds on a page
END_MARGIN = 1.0        # warn when a timestamp is this close to the end of the audio

_SECONDS_RE = re.compile(r"^(\d+(?:\.\d+)?|\.\d+)$")
_MS_RE = re.compile(r"^(\d+):(\d{2})(\.\d+)?$")
_HMS_RE = re.compile(r"^(\d+):(\d{2}):(\d{2})(\.\d+)?$")


class TimingError(ValueError):
    """Timestamps are missing, malformed, or do not fit the song."""


def parse_timestamp(value) -> float:
    """Parse one timestamp into seconds. Accepts numbers and m:ss, mm:ss.s, h:mm:ss, or seconds strings."""
    if isinstance(value, bool):
        raise TimingError(f"Bad timestamp {value!r}: {FORMATS_HINT}.")
    if isinstance(value, (int, float)):
        if not math.isfinite(value) or value < 0:
            raise TimingError(f"Bad timestamp {value!r}: it must be zero or more seconds.")
        return float(value)
    if not isinstance(value, str):
        raise TimingError(f"Bad timestamp {value!r}: {FORMATS_HINT}.")
    s = value.strip()
    if m := _SECONDS_RE.match(s):
        return float(s)
    if m := _MS_RE.match(s):
        mins, secs, frac = int(m.group(1)), int(m.group(2)), m.group(3) or ""
        if secs >= 60:
            raise TimingError(f"Bad timestamp \"{s}\": seconds must be 00-59.")
        return mins * 60 + secs + (float(frac) if frac else 0.0)
    if m := _HMS_RE.match(s):
        h, mins, secs, frac = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4) or ""
        if mins >= 60 or secs >= 60:
            raise TimingError(f"Bad timestamp \"{s}\": minutes and seconds must be 00-59 in h:mm:ss.")
        return h * 3600 + mins * 60 + secs + (float(frac) if frac else 0.0)
    if s.startswith("-"):
        raise TimingError(f"Bad timestamp \"{s}\": it cannot be negative.")
    if re.match(r"^\d+:\d$", s):
        raise TimingError(f"Bad timestamp \"{s}\": write seconds with two digits, like {s[:-1]}0{s[-1]}.")
    raise TimingError(f"Bad timestamp \"{s}\": {FORMATS_HINT}.")


def format_timestamp(seconds: float) -> str:
    """Format seconds as m:ss, with one decimal when needed (1:05.5)."""
    tenths = round(seconds * 10)
    whole, frac = divmod(tenths, 10)
    h, rem = divmod(whole, 3600)
    m, s = divmod(rem, 60)
    text = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    return text + (f".{frac}" if frac else "")


def parse_inline(text: str) -> list:
    return [p for p in re.split(r"[,\s]+", text.strip()) if p]


def load_turns_file(path: str | Path) -> tuple[list, dict | None]:
    """Read a turns file. Returns the raw timestamp values and the optional per-line times.

    A .json file holds {"turns": [...], "lines": {"2": [...]}} or a plain list. Any other file is
    text: one timestamp per line, with # comments and blank lines ignored.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise TimingError(f"Turns file not found: {path}") from None
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise TimingError(f"{path} is not valid JSON: {e}") from None
        if isinstance(data, list):
            return data, None
        if not isinstance(data, dict) or not isinstance(data.get("turns"), list):
            raise TimingError(f"{path}: expected {{\"turns\": [\"0:03\", \"0:10\", ...]}}.")
        lines = data.get("lines")
        if lines is not None and not isinstance(lines, dict):
            raise TimingError(f"{path}: \"lines\" must map page numbers to lists of times, "
                              f"like {{\"2\": [\"0:03.5\", \"0:06\"]}}.")
        return data["turns"], lines
    values = []
    for line in raw.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            values.append(line)
    return values, None


def _short(text: str, width: int = 48) -> str:
    return text if len(text) <= width else text[: width - 3].rstrip() + "..."


def page_listing(pages: list[Page], values: list[str] | None = None) -> str:
    """List the pages that timestamps map to (every page after the first)."""
    rows = []
    for i, p in enumerate(pages[1:]):
        first = f"\"{_short(p.first_line)}\"" if p.first_line else ("(no lines)" if p.kind == "section" else "")
        row = f"  Page {p.number:<3} {p.label:<13} {first}".rstrip()
        if values is not None:
            given = str(values[i]) if i < len(values) else "missing"
            row = f"{row:<76} <- {given}"
        rows.append(row)
    if values is not None and len(values) > len(pages) - 1:
        for v in values[len(pages) - 1:]:
            rows.append(f"  {'(no page)':<74} <- {v} (extra)")
    return "\n".join(rows)


def count_error(pages: list[Page], values: list) -> str:
    need = len(pages) - 1
    first = pages[0]
    msg = [f"{need} timestamps expected, got {len(values)}.",
           f"Give one timestamp for every page except page 1 ({first.label}, shown from 0:00): "
           f"the time that page starts (its turn runs from 0.25 s before to 0.45 s after).",
           "The timestamps map to these pages:",
           page_listing(pages, [str(v) for v in values])]
    diff = len(values) - need
    if diff in (1, 2) or diff in (-1, -2):
        msg.append("If the timing file was made with a different --no-cover / --no-back-cover setting, "
                   "use the same setting here.")
    return "\n".join(msg)


def validate_turns(pages: list[Page], values: list, audio_seconds: float) -> tuple[list[float], list[str]]:
    """Check timestamps against the pages and the audio. Returns page start times and warnings."""
    if len(values) != len(pages) - 1:
        raise TimingError(count_error(pages, values))
    turns = []
    errors = []
    for v, p in zip(values, pages[1:]):
        try:
            turns.append(parse_timestamp(v))
        except TimingError as e:
            errors.append(f"Page {p.number} ({p.label}): {e}")
    if errors:
        raise TimingError("\n".join(errors))
    if turns and all(t == 0 for t in turns):
        raise TimingError("Every timestamp is 0:00. Replace the placeholders from init-timing with the real "
                          "times each page starts.\n" + page_listing(pages))
    if turns and turns[0] <= 0:
        errors.append(f"Page {pages[1].number} ({pages[1].label}) starts at 0:00, but page 1 is already shown "
                      f"from 0:00. The first timestamp must be later than 0:00.")
    for a, b, pa, pb in zip(turns, turns[1:], pages[1:], pages[2:]):
        if b <= a:
            errors.append(f"Page {pb.number} ({pb.label}) at {format_timestamp(b)} is not after "
                          f"page {pa.number} ({pa.label}) at {format_timestamp(a)}. Timestamps must strictly increase.")
    for t, p in zip(turns, pages[1:]):
        if t >= audio_seconds:
            errors.append(f"Page {p.number} ({p.label}) at {format_timestamp(t)} is at or after the end of the "
                          f"audio ({format_timestamp(audio_seconds)}).")
    if errors:
        raise TimingError("\n".join(errors))

    starts = [0.0] + turns
    warnings = []
    for i, p in enumerate(pages):
        end = starts[i + 1] if i + 1 < len(starts) else audio_seconds
        if end - starts[i] < MIN_SECTION:
            warnings.append(f"Page {p.number} ({p.label}) is on screen for only {end - starts[i]:.1f} s "
                            f"({format_timestamp(starts[i])} to {format_timestamp(end)}).")
    for t, p in zip(turns, pages[1:]):
        if audio_seconds - t < END_MARGIN:
            warnings.append(f"Page {p.number} ({p.label}) at {format_timestamp(t)} is within {END_MARGIN:.0f} s "
                            f"of the end of the audio ({format_timestamp(audio_seconds)}).")
    return starts, warnings


def line_times(pages: list[Page], starts: list[float], audio_seconds: float, mode: str = "all",
               custom: dict | None = None) -> list[list[list[float]] | None]:
    """Start and end of each lyric line, per page. None for a page means: show all lines at once."""
    if mode not in ("even", "all"):
        raise TimingError(f"Unknown line timing {mode!r}: use even or all.")
    custom = _parse_custom_lines(pages, starts, audio_seconds, custom or {})
    out: list[list[list[float]] | None] = []
    for i, p in enumerate(pages):
        n = len(p.lines)
        start = starts[i]
        end = starts[i + 1] if i + 1 < len(starts) else audio_seconds
        if n == 0:
            out.append([])
        elif p.number in custom:
            ts = custom[p.number]
            out.append([[t, ts[k + 1] if k + 1 < n else end] for k, t in enumerate(ts)])
        elif mode == "all":
            out.append(None)
        else:
            span = max(end - start - LINE_LEAD - LINE_TAIL, 0.5) / n
            out.append([[start + LINE_LEAD + k * span, start + LINE_LEAD + (k + 1) * span] for k in range(n)])
    return out


def _parse_custom_lines(pages, starts, audio_seconds, custom: dict) -> dict[int, list[float]]:
    by_number = {p.number: (i, p) for i, p in enumerate(pages)}
    out = {}
    errors = []
    for key, values in custom.items():
        try:
            number = int(str(key).strip())
        except ValueError:
            errors.append(f"lines: \"{key}\" is not a page number.")
            continue
        if number not in by_number:
            errors.append(f"lines: there is no page {number}.")
            continue
        i, p = by_number[number]
        if not isinstance(values, list) or len(values) != len(p.lines):
            got = len(values) if isinstance(values, list) else "not a list"
            errors.append(f"lines: page {number} ({p.label}) has {len(p.lines)} lines, got {got} times.")
            continue
        start = starts[i]
        end = starts[i + 1] if i + 1 < len(starts) else audio_seconds
        try:
            ts = [parse_timestamp(v) for v in values]
        except TimingError as e:
            errors.append(f"lines: page {number}: {e}")
            continue
        if any(b <= a for a, b in zip(ts, ts[1:])):
            errors.append(f"lines: page {number} line times must strictly increase.")
        elif ts[0] < start or ts[-1] >= end:
            errors.append(f"lines: page {number} line times must be within the page "
                          f"({format_timestamp(start)} to {format_timestamp(end)}).")
        else:
            out[number] = ts
    if errors:
        raise TimingError("\n".join(errors))
    return out


def timing_template(pages: list[Page], title: str, flags: str = "", times: list[float] | None = None,
                    header: str = "") -> str:
    """The init-timing file: one commented line and one timestamp per page after the first.

    Without times every timestamp is a 00:00 placeholder.
    """
    out = [f"# Page-turn timestamps for \"{title}\"" + (f" (made with {flags})" if flags else "")]
    if header:
        out += header.rstrip("\n").split("\n")
    out += ["# Replace each 00:00 with the time that page starts. The turn into it runs from 0.25 s before to 0.45 s after."
            if times is None else "# Each time is when that page starts. The turn into it runs from 0.25 s before to 0.45 s after.",
           f"# Formats: m:ss, mm:ss, mm:ss.s, h:mm:ss, or seconds (74.5). Lines starting with # are ignored.",
           f"# {len(pages) - 1} timestamps for {len(pages)} pages.",
           "",
           f"# page 1: {pages[0].label} - shown from 0:00, no timestamp needed" +
           (f" (\"{pages[0].first_line}\")" if pages[0].first_line else ""),
           ""]
    for i, p in enumerate(pages[1:]):
        desc = f"# page {p.number}: {p.label}"
        if p.first_line:
            desc += f" - \"{p.first_line}\""
        elif p.kind == "section":
            desc += " - (no lines)"
        out += [desc, "00:00" if times is None else format_timestamp(times[i]), ""]
    return "\n".join(out)
