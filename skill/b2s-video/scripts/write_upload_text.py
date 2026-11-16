"""Write the YouTube upload text from a song JSON as a plain text file, ready to copy and paste.

The text comes from the "youtube" block that the video-upload-metadata skill adds to a version in
the song JSON. Nothing here invents text: it only lays out what the JSON holds, with no JSON quotes,
brackets or escapes, so each part can be pasted straight into YouTube Studio.

    python write_upload_text.py --song song.json --out out/<folder>-youtube.txt [--version "Title"] [--force]

Standard library only, so any Python 3.8+ runs it (the main venv's is fine).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULE = "=" * 60
PLACEHOLDER = re.compile(r"\{[A-Z_]+\}")


def pick_version(song: dict, wanted: str | None) -> dict:
    versions = song.get("versions") or [song]
    with_yt = [v for v in versions if isinstance(v.get("youtube"), dict)]
    if wanted:
        for v in versions:
            if v.get("title", "").casefold() == wanted.casefold():
                if "youtube" not in v:
                    sys.exit(f'error: version "{wanted}" has no "youtube" block; run the video-upload-metadata skill first.')
                return v
        sys.exit(f'error: no version titled "{wanted}". Titles: ' + ", ".join(v.get("title", "?") for v in versions))
    if not with_yt:
        sys.exit('error: the song JSON has no "youtube" block; run the video-upload-metadata skill first.')
    if len(with_yt) > 1:
        sys.exit("error: several versions have a youtube block; pass --version. Titles: "
                 + ", ".join(v.get("title", "?") for v in with_yt))
    return with_yt[0]


def as_text(value) -> str:
    """Descriptions are stored as a list of lines (or a single string)."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(x) for x in value)
    return str(value)


def section(label: str, body: str, note: str = "") -> list[str]:
    head = f"--- {label} ---" + (f"  ({note})" if note else "")
    return [head, body.strip("\n"), ""]


def tag_chars(tags: list[str]) -> int:
    # YouTube counts quotes around a tag with spaces, plus the commas between tags.
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(len(tags) - 1, 0)


def part(name: str, video_hint: str, part_yt: dict, shared: dict) -> list[str]:
    """One upload (regular video or Short). Fields missing from the part fall back to the
    shared top level of the youtube block, which is how older song JSONs stored them."""
    get = lambda key: part_yt.get(key, shared.get(key))
    out = [RULE, f"{name}   ({video_hint})", RULE, ""]

    title = get("title")
    if title and "\n" in title:
        out += section("TITLE OPTIONS (pick one)", title)
    elif title:
        out += section("TITLE", title, f"{len(title)}/100")
    desc = as_text(get("description"))
    if desc:
        out += section("DESCRIPTION", desc, f"{len(desc)}/5000")
    tags = get("tags") or []
    if tags:
        out += section("TAGS (paste into the Tags box)", ", ".join(tags), f"{tag_chars(tags)}/500")
    if part_yt.get("thumbnail_text"):
        out += section("THUMBNAIL TEXT", part_yt["thumbnail_text"])
    if get("pinned_comment"):
        out += section("PINNED COMMENT", get("pinned_comment"))
    settings = part_yt.get("studio_settings") or {}
    if settings:
        lines = [f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in settings.items()]
        out += section("STUDIO SETTINGS", "\n".join(lines))
    return out


def from_flat(yt: dict) -> dict:
    """The video-upload-metadata skill's own file layout (<folder>.metadata.json): one flat block
    with a list of title options and optional shorts_title / shorts_description."""
    titles = yt.get("titles") or ([yt["title"]] if yt.get("title") else [])
    settings = {k: yt[k] for k in ("made_for_kids", "altered_or_synthetic", "category", "language", "playlist") if k in yt}
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--song", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--version", help="version title, when several versions have a youtube block")
    ap.add_argument("--force", action="store_true", help="replace an existing file that this script did not write")
    a = ap.parse_args()

    song = json.loads(a.song.read_text(encoding="utf-8"))
    v = pick_version(song, a.version)
    yt = v["youtube"]
    folder = a.song.parent.name
    title = v.get("title", folder)

    if a.out.exists() and not a.force:
        first = a.out.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        if not first or not first[0].startswith("YouTube upload text for"):
            sys.exit(f"error: {a.out} exists and was not written by this script; pass --force to replace it.")

    lines = [f'YouTube upload text for "{title}"',
             f"Made from the youtube block in {a.song.name}. Edit the JSON, not this file, then run the script again.",
             ""]
    if "normal" not in yt and "short" not in yt and ("titles" in yt or "description" in yt):
        yt = from_flat(yt)
    if isinstance(yt.get("normal"), dict):
        lines += part("REGULAR VIDEO", f"{folder}-16x9.mp4 + {folder}-thumbnail.jpg", yt["normal"], yt)
    if isinstance(yt.get("short"), dict):
        lines += part("SHORT", f"{folder}-short-*.mp4 + {folder}-thumbnail-9x16.jpg", yt["short"], yt)
    if len(lines) == 3:
        sys.exit('error: the youtube block has neither "normal" nor "short".')

    text = "\n".join(lines).rstrip() + "\n"
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8")
    print(f"Wrote {a.out}")
    left = sorted(set(PLACEHOLDER.findall(text)))
    if left:
        print("Placeholders still to fill in: " + ", ".join(left))
    return 0


if __name__ == "__main__":
    sys.exit(main())
