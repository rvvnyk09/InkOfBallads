"""YouTube upload text: the song JSON's "youtube" block laid out as plain text, ready to paste.

The block is what the video-upload-metadata skill adds to a version in the song JSON. Nothing here
invents text: it only lays out what the JSON holds, with no JSON quotes, brackets or escapes, so each
part can be pasted straight into YouTube Studio.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .song import SongError, select_version

RULE = "=" * 60
PLACEHOLDER = re.compile(r"\{[A-Z_]+\}")
FIRST_LINE = "YouTube upload text for"


def read_json(path: str | Path) -> dict:
    path = Path(path)
    try:
        song = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise SongError(f"Song file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise SongError(f"{path} is not valid JSON: {e}") from None
    if not isinstance(song, dict):
        raise SongError(f"{path}: the top level must be a JSON object.")
    return song


def pick_version(song: dict, choice: str | None = None) -> dict:
    """The version whose youtube block to write. With --version (number, channel or title) that
    version; otherwise the one version that has a youtube block."""
    versions = [v for v in song.get("versions") or [song] if isinstance(v, dict)]
    if choice:
        if not isinstance(song.get("versions"), list):
            raise SongError(f"--version {choice}: the song file has no \"versions\" array, only one song.")
        picked = select_version(song, choice)
        if not isinstance(picked.get("youtube"), dict):
            raise SongError(f'version "{picked.get("title", choice)}" has no "youtube" block; '
                            f"run the video-upload-metadata skill first.")
        return picked
    with_yt = [v for v in versions if isinstance(v.get("youtube"), dict)]
    if not with_yt:
        raise SongError('the song JSON has no "youtube" block; run the video-upload-metadata skill first.')
    if len(with_yt) > 1:
        raise SongError("several versions have a youtube block; pass --version. Titles: "
                        + ", ".join(v.get("title", "?") for v in with_yt))
    return with_yt[0]


def as_text(value) -> str:
    """Descriptions are stored as a list of lines (or a single string)."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(x) for x in value)
    return str(value)


def _section(label: str, body: str, note: str = "") -> list[str]:
    head = f"--- {label} ---" + (f"  ({note})" if note else "")
    return [head, body.strip("\n"), ""]


def tag_chars(tags: list[str]) -> int:
    """Characters YouTube counts against its 500 limit: quotes around a tag with spaces, plus commas."""
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(len(tags) - 1, 0)


def _part(name: str, video_hint: str, part_yt: dict, shared: dict) -> list[str]:
    """One upload (regular video or Short). Fields missing from the part fall back to the shared
    top level of the youtube block, which is how older song JSONs stored them."""
    def get(key):
        return part_yt.get(key, shared.get(key))
    out = [RULE, f"{name}   ({video_hint})", RULE, ""]

    title = get("title")
    if title and "\n" in title:
        out += _section("TITLE OPTIONS (pick one)", title)
    elif title:
        out += _section("TITLE", title, f"{len(title)}/100")
    desc = as_text(get("description"))
    if desc:
        out += _section("DESCRIPTION", desc, f"{len(desc)}/5000")
    tags = get("tags") or []
    if tags:
        out += _section("TAGS (paste into the Tags box)", ", ".join(tags), f"{tag_chars(tags)}/500")
    if part_yt.get("thumbnail_text"):
        out += _section("THUMBNAIL TEXT", part_yt["thumbnail_text"])
    if get("pinned_comment"):
        out += _section("PINNED COMMENT", get("pinned_comment"))
    settings = part_yt.get("studio_settings") or {}
    if settings:
        out += _section("STUDIO SETTINGS", "\n".join(f"{k.replace('_', ' ').capitalize()}: {v}"
                                                     for k, v in settings.items()))
    return out


def from_flat(yt: dict) -> dict:
    """The video-upload-metadata skill's own flat layout: a list of title options and optional
    shorts_title / shorts_description, turned into {"normal": ..., "short": ...}."""
    titles = yt.get("titles") or ([yt["title"]] if yt.get("title") else [])
    settings = {k: yt[k] for k in ("made_for_kids", "altered_or_synthetic", "category", "language", "playlist")
                if k in yt}
    thumb = yt.get("thumbnail_text")
    normal = {
        "title": "\n".join(f"{t}   [{len(t)}/100]" if len(titles) > 1 else t for t in titles) or None,
        "description": yt.get("description"),
        "tags": yt.get("tags"),
        "thumbnail_text": " / ".join(thumb) if isinstance(thumb, list) else thumb,
        "studio_settings": settings,
    }
    out = {"normal": {k: v for k, v in normal.items() if v}}
    if yt.get("shorts_title") or yt.get("shorts_description"):
        out["short"] = {k: v for k, v in {"title": yt.get("shorts_title"), "description": yt.get("shorts_description"),
                                          "tags": yt.get("tags"), "studio_settings": settings}.items() if v}
    return out


def upload_text(version: dict, json_name: str, folder: str) -> str:
    """The whole text file for one version. folder names the output videos (<folder>-16x9.mp4 ...)."""
    yt = version["youtube"]
    lines = [f'{FIRST_LINE} "{version.get("title", folder)}"',
             f"Made from the youtube block in {json_name}. Edit the JSON, not this file, then run b2s-video upload-text again.",
             ""]
    if "normal" not in yt and "short" not in yt and ("titles" in yt or "description" in yt):
        yt = from_flat(yt)
    if isinstance(yt.get("normal"), dict):
        lines += _part("REGULAR VIDEO", f"{folder}-16x9.mp4 + {folder}-thumbnail.jpg", yt["normal"], yt)
    if isinstance(yt.get("short"), dict):
        lines += _part("SHORT", f"{folder}-short-*.mp4 + {folder}-thumbnail-9x16.jpg", yt["short"], yt)
    if len(lines) == 3:
        raise SongError('the youtube block has neither "normal" nor "short".')
    return "\n".join(lines).rstrip() + "\n"


def placeholders(text: str) -> list[str]:
    """{PLACEHOLDER}s still to fill in, such as {FULL_VIDEO_URL}."""
    return sorted(set(PLACEHOLDER.findall(text)))


def keep_filled(old: str, new: str) -> tuple[str, list[str]]:
    """Carry over placeholders the user filled in by hand in the previous file (a real link pasted
    over {FULL_VIDEO_URL}, say), so making the file again does not lose them. A line of the new text
    that holds placeholders is matched against every line of the old file with the placeholders as
    wildcards; where one matches, the old values are kept. Returns the text and the names kept."""
    old_lines = old.splitlines()
    kept: list[str] = []
    out = []
    for line in new.split("\n"):
        names = PLACEHOLDER.findall(line)
        if names:
            parts = PLACEHOLDER.split(line)                       # one more part than names
            pattern = re.compile("(.+?)".join(re.escape(p) for p in parts))
            for o in old_lines:
                m = pattern.fullmatch(o)
                if m and m.groups() != tuple(names):
                    values = m.groups()
                    kept += [n for n, v in zip(names, values) if v != n]
                    line = "".join(p + (values[i] if i < len(values) else "") for i, p in enumerate(parts))
                    break
        out.append(line)
    return "\n".join(out), kept


def written_by_us(path: Path) -> bool:
    first = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
    return bool(first) and first[0].startswith(FIRST_LINE)


def default_out(song_path: str | Path) -> Path:
    """<song folder>/out/<folder>-youtube.txt, beside the videos."""
    folder = Path(song_path).resolve().parent
    return folder / "out" / f"{folder.name}-youtube.txt"
