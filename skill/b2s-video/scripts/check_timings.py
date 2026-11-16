"""Check page-turn timestamps against what is actually sung, and suggest a Short.

Run it with the alignment venv's Python (it needs b2s_video and stable-ts / Whisper):

    <program>/.venv-align/Scripts/python.exe check_timings.py --song song.json --audio song.mp3 --turns turns.txt

For every page turn it shows the words sung around it and says CLASH when a word is being sung
while the page swings (from 0.25 s before the timestamp to 0.45 s after). For a clash, or when the
page's own first words were found elsewhere, it suggests a better time: about 0.6 s before the
page's first sung word, and never before the last word of the section before has ended.

--write FILE saves a timing file with the suggested times (it never overwrites without --force).
The Whisper transcription is cached next to the audio (<audio>.words.json), so reruns are quick.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

LEAD, TAIL = 0.25, 0.45      # the turn runs from LEAD s before a timestamp to TAIL s after it (notebook.html)


def word_cap(text: str) -> float:
    """Longest believable length of a sung word. Whisper often stretches a word's start back over
    the pause before it ("A" in "A little John" timed at 1.7 s), which would hide the gap between
    two sections, so the start is pulled forward to at most this long before the word's end."""
    return min(0.8, 0.25 + 0.1 * len(norm(text)))


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def transcribe(audio: Path, model: str) -> list[dict]:
    cache = audio.with_name(audio.name + ".words.json")
    stamp = audio.stat().st_mtime
    if cache.is_file():
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("mtime") == stamp and data.get("model") == model and data.get("v") == 2:
            return data["words"]
    import stable_whisper
    print(f"Transcribing {audio.name} with Whisper {model} (about a minute)...", file=sys.stderr)
    result = stable_whisper.load_model(model).transcribe(str(audio), language="en", word_timestamps=True, verbose=None)
    words = []
    for seg in result.segments:
        if re.fullmatch(r"\W*(music|instrumental)\W*", seg.text.strip(), re.IGNORECASE):
            continue                               # Whisper's label for a stretch without singing
        for w in seg.words:
            if norm(w.word):
                end = float(w.end)
                words.append({"text": w.word.strip(), "start": max(float(w.start), end - word_cap(w.word)),
                              "end": end, "p": round(float(w.probability), 2)})
    cache.write_text(json.dumps({"v": 2, "mtime": stamp, "model": model, "words": words}, indent=1), encoding="utf-8")
    return words


def find_first_words(line: str, words: list[dict], near: float, span: float = 9.0) -> int | None:
    """Index of the word where `line` starts, searching near the given time. Whisper mishears
    (Merry -> Mary), so this matches the first few words loosely."""
    target = " ".join(norm(t) for t in line.split()[:4] if norm(t))
    best, best_score = None, 0.0
    for i, w in enumerate(words):
        if abs(w["start"] - near) > span:
            continue
        heard = " ".join(norm(x["text"]) for x in words[i:i + 4])
        score = difflib.SequenceMatcher(None, target, heard).ratio() - abs(w["start"] - near) / 100
        if score > best_score:
            best, best_score = i, score
    return best if best_score >= 0.55 else None


def fmt(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--song", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--turns", required=True, help="the timing file to check")
    ap.add_argument("--version", help="for a song file with several versions")
    ap.add_argument("--no-cover", action="store_true")
    ap.add_argument("--no-back-cover", action="store_true")
    ap.add_argument("--model", default="base", help="Whisper model (default base)")
    ap.add_argument("--write", help="save a timing file with the suggested times")
    ap.add_argument("--force", action="store_true", help="let --write overwrite an existing file")
    a = ap.parse_args()

    from b2s_video.render import probe_duration
    from b2s_video.song import build_pages, load_song, song_title
    from b2s_video.timing import load_turns_file, timing_template, validate_turns

    audio = Path(a.audio)
    song = load_song(a.song, a.version, audio)
    pages = build_pages(song, cover=not a.no_cover, back=not a.no_back_cover)
    total = probe_duration(audio)
    values, _ = load_turns_file(a.turns)
    starts, _ = validate_turns(pages, values, total)
    words = transcribe(audio, a.model)
    if not words:
        print("Whisper heard no words; check the audio.", file=sys.stderr)
        return 1
    sung_end = words[-1]["end"]

    print(f'"{song_title(song)}": {len(pages)} pages, audio {fmt(total)}, singing ends {fmt(sung_end)}\n')
    suggested, problems = [], 0
    for j in range(1, len(pages)):
        p, t = pages[j], starts[j]
        lo, hi = t - LEAD, t + TAIL
        clash = [w for w in words if w["start"] < hi and w["end"] > lo]
        new, note = t, ""
        first = find_first_words(p.first_line, words, t) if p.first_line else None
        gap = lambda i: words[i]["start"] - words[i - 1]["end"] if i else 99.0
        if first and gap(first) < 0.15:
            # The singer may add a word before the written line ("A little John"): when the match
            # runs straight on from the word before, the section starts at a clear pause just before it.
            back = [i for i in (first - 1, first - 2) if i >= 0 and gap(i) > 0.6]
            first = back[0] if back else first
        if first is not None:
            fw = words[first]["start"]
            pe = words[first - 1]["end"] if first else 0.0
            ideal = fw - 0.6                       # the turn ends 0.15 s before the first word
            if ideal - LEAD >= pe:
                new = ideal
            else:                                  # tight gap: centre the swing on it
                new = (pe + fw) / 2 - (TAIL - LEAD) / 2
            note = f'first words heard at {fmt(fw)} ("{" ".join(x["text"] for x in words[first:first + 3])}"), ' \
                   f'previous word ends {fmt(pe)}'
            if fw - pe < LEAD + TAIL:
                note += f"; gap only {fw - pe:.1f} s, the swing cannot fit fully"
        elif p.kind == "back":
            if lo < sung_end:
                new = sung_end + 0.6
            note = f"singing ends {fmt(sung_end)}"
        elif clash:
            # Whisper missed this page's words: at least start the turn after the words it clashes with.
            new = max(w["end"] for w in clash) + LEAD + 0.1
            note = "first words not heard: moved after the clashing words; check by ear"
        else:
            note = "first words not heard near this time: check by ear"
        tight = "cannot fit" in note
        if (not clash and abs(new - t) < 0.4) or (clash and tight and abs(new - t) < 0.3):
            new = t                                # close enough; keep the user's time
        new = max(new, (suggested[-1] + 0.8) if suggested else 0.1)
        new = min(new, total - 1.0)
        suggested.append(round(new, 1))
        status = ("tight" if tight and new == t else "CLASH") if clash else "ok"
        problems += new != t
        print(f"Page {p.number:<3} {p.label:<12} {fmt(t):>7}  {status:<5}  suggest {fmt(new):>7}")
        if clash:
            print("            sung during the turn: " + " ".join(f'{w["text"]}({fmt(w["start"])})' for w in clash))
        print(f"            {note}")

    # A Short: the cover opening, the first section(s) and the first chorus or hook.
    sec = [i for i, p in enumerate(pages) if p.kind == "section"]
    chorus = next((i for i in sec if pages[i].repeated), None)
    last = chorus if chorus is not None else sec[min(1, len(sec) - 1)]
    final = [starts[0]] + suggested
    begin = max(0.0, final[sec[0]] - LEAD - 0.05)
    stop = final[last + 1] - LEAD - 0.05 if last + 1 < len(pages) else total
    tail = [w for w in words if begin < w["end"] <= stop]
    print(f"\nShort: pages {sec[0] + 1}-{last + 1} ({pages[last].label} ends it): start {begin:.1f} s, "
          f"length {stop - begin:.1f} s")
    if tail:
        print(f'  last word inside: "{tail[-1]["text"]}" ends {fmt(tail[-1]["end"])} '
              f"({stop - tail[-1]['end']:.1f} s before the Short ends)")
    print(f"  ffmpeg -y -ss {begin:.1f} -i <full-9x16.mp4> -t {stop - begin:.1f} -c:v libx264 -crf 20 "
          f"-pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart <short.mp4>")
    if stop - begin > 60:
        print("  Over 60 s: end at an earlier page, or start later, for Shorts.")

    print(f"\n{problems} page(s) to move." if problems else "\nAll turns fall between sung words.")
    if a.write:
        out = Path(a.write)
        if out.exists() and not a.force:
            print(f"{out} exists; not overwritten (use --force).", file=sys.stderr)
            return 1
        flags = " ".join(f for f, on in (("--no-cover", a.no_cover), ("--no-back-cover", a.no_back_cover)) if on)
        header = "# Checked against a Whisper word transcription by check_timings.py."
        out.write_text(timing_template(pages, song_title(song), flags, times=suggested, header=header) + "\n",
                       encoding="utf-8")
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
