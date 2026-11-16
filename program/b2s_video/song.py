"""Read a b2s song JSON and turn it into the list of book pages."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# The tags the b2s skill writes. Any other [Tag] is accepted too.
KNOWN_TAGS = (
    "Intro", "Verse", "Pre-chorus", "Chorus", "Hook", "Drop", "Bridge", "Solo",
    "Build-up", "Instrumental", "Breakdown", "Break", "Interlude", "Outro",
)
_KNOWN_LOWER = {t.lower() for t in KNOWN_TAGS}

TAG_RE = re.compile(r"^\s*\[\s*(.*?)\s*\]\s*$")
# "Chorus", "Chorus 2", "Final Chorus", "Hook x2" are repeated sections; "Pre-chorus" and "Post-chorus" are not.
REPEATED_RE = re.compile(r"^(?:(?:final|last|double|repeat)\s+)?(?:chorus|hook)\b(?!-)", re.IGNORECASE)


class SongError(ValueError):
    """The song JSON cannot be used."""


@dataclass
class Section:
    tag: str | None
    lines: list[str] = field(default_factory=list)


@dataclass
class Page:
    kind: str                  # "cover", "section" or "back"
    number: int                # 1-based position in the book
    tag: str | None = None
    lines: list[str] = field(default_factory=list)

    @property
    def repeated(self) -> bool:
        return self.kind == "section" and bool(self.tag) and bool(REPEATED_RE.match(self.tag))

    @property
    def label(self) -> str:
        if self.kind == "cover":
            return "Cover"
        if self.kind == "back":
            return "Back cover"
        return self.tag or "(no tag)"

    @property
    def first_line(self) -> str:
        return self.lines[0] if self.lines else ""


def typographic(text: str) -> str:
    """Display form of a text: straight apostrophes become typographic ones. Words are never changed."""
    return text.replace("'", "’")


def cover_work(work: str) -> str:
    """source.work as the cover shows it: without a bracketed note at the end, such as
    "The sinking of RMS Titanic (historical event, April 1912)". The note stays in the JSON."""
    return re.sub(r"\s*\([^()]*\)\s*$", "", work).strip() or work


def load_song(path: str | Path, version: str | None = None, audio: str | Path | None = None) -> dict:
    """Read a song JSON. A file with a "versions" array holds several songs; one is picked by
    select_version (from --version, or from the audio file name)."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise SongError(f"Song file not found: {path}") from None
    try:
        song = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SongError(f"{path} is not valid JSON: {e}") from None
    if not isinstance(song, dict):
        raise SongError(f"{path}: the top level must be a JSON object with a \"lyrics\" array.")
    if isinstance(song.get("versions"), list):
        song = select_version(song, version, audio)
    elif version:
        raise SongError(f"--version {version}: {path} has no \"versions\" array, only one song.")
    if "lyrics" not in song:
        raise SongError(f"{path}: no \"lyrics\" field. It must be an array of strings, one line per entry.")
    song.setdefault("_file_stem", path.stem)
    return song


def _letters(text) -> str:
    return re.sub(r"[^0-9a-z]", "", str(text).lower())


def select_version(song: dict, choice: str | None = None, audio: str | Path | None = None) -> dict:
    """Pick one entry of song["versions"] and merge it over the shared top-level fields.

    choice may be a 1-based number, a channel ("kids", "general") or a title. Without a choice,
    a single version is used, or the one whose title matches the audio file name.
    """
    versions = [v for v in song["versions"] if isinstance(v, dict)]
    if not versions:
        raise SongError("\"versions\" is empty.")

    def listing() -> str:
        return "\n".join(f"  {i}. {v.get('title', '(no title)')} ({v.get('channel', 'no channel')})"
                         for i, v in enumerate(versions, start=1))

    picked = None
    if choice:
        c = str(choice).strip()
        if c.isdigit() and 1 <= int(c) <= len(versions):
            picked = versions[int(c) - 1]
        else:
            matches = [v for v in versions if _letters(c) in (_letters(v.get("title", "")), _letters(v.get("channel", "")))]
            if len(matches) == 1:
                picked = matches[0]
        if picked is None:
            raise SongError(f"--version {c} matches no single version. Use a number, channel or title:\n{listing()}")
    elif len(versions) == 1:
        picked = versions[0]
    else:
        stem = _letters(Path(audio).stem) if audio else ""
        matches = [v for v in versions if stem and _letters(v.get("title", "")) == stem]
        if len(matches) == 1:
            picked = matches[0]
        else:
            raise SongError(f"This song file has {len(versions)} versions. Choose one with --version "
                            f"(a number, channel or title):\n{listing()}")
    merged = {k: v for k, v in song.items() if k != "versions"}
    merged.update(picked)
    return merged


def lyric_entries(song: dict) -> list[str]:
    lyrics = song.get("lyrics")
    if isinstance(lyrics, str):          # tolerate one string with newlines
        lyrics = lyrics.splitlines()
    if not isinstance(lyrics, list):
        raise SongError("\"lyrics\" must be an array of strings.")
    out = []
    for i, entry in enumerate(lyrics):
        if entry is None:
            entry = ""
        if not isinstance(entry, str):
            raise SongError(f"lyrics[{i}] is {type(entry).__name__}, expected a string.")
        out.append(entry)
    return out


def parse_sections(lyrics: list[str]) -> list[Section]:
    """Split lyric entries into sections.

    A [Tag] entry starts a section, an empty string ends one. Lines before any tag, or after
    an empty string with no new tag, form a section without a tag.
    """
    sections: list[Section] = []
    open_section: Section | None = None
    for entry in lyrics:
        m = TAG_RE.match(entry)
        if m:
            open_section = Section(tag=m.group(1) or None)
            sections.append(open_section)
        elif entry.strip() == "":
            open_section = None
        else:
            if open_section is None:
                open_section = Section(tag=None)
                sections.append(open_section)
            open_section.lines.append(entry.strip())
    return sections


def unknown_tags(sections: list[Section]) -> list[str]:
    seen = []
    for s in sections:
        if s.tag is None:
            continue
        base = s.tag.split(":")[0].strip().lower()                 # "Verse 2: soft" -> "verse 2"
        base = re.sub(r"\s*(?:x\s*)?\d+$", "", base)                # "verse 2" -> "verse"
        base = re.sub(r"^(final|last|double|repeat)\s+", "", base)
        if base not in _KNOWN_LOWER and s.tag not in seen:
            seen.append(s.tag)
    return seen


def build_pages(song: dict, cover: bool = True, back: bool = True) -> list[Page]:
    sections = parse_sections(lyric_entries(song))
    if not sections:
        raise SongError("The lyrics have no sections or lines, so there is nothing to put on a page.")
    pages: list[Page] = []
    if cover:
        pages.append(Page(kind="cover", number=0))
    for s in sections:
        pages.append(Page(kind="section", number=0, tag=s.tag, lines=list(s.lines)))
    if back:
        pages.append(Page(kind="back", number=0))
    for i, p in enumerate(pages, start=1):
        p.number = i
    return pages


def song_title(song: dict) -> str:
    title = song.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    stem = song.get("_file_stem") or "Untitled"
    return re.sub(r"[-_]+", " ", stem).strip().title() or "Untitled"


def source_field(song: dict, key: str) -> str | None:
    src = song.get("source")
    if not isinstance(src, dict):
        return None
    value = src.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


LOOKS = ("notebook", "kids", "classic")


def default_look(song: dict) -> str:
    """The spiral notebook, for every channel. kids and classic are the earlier storybook looks."""
    return "notebook"
