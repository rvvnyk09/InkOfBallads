"""Optional: suggest page-turn timestamps with local forced alignment (stable-ts, optionally Demucs).

The output is only a starting point. render always uses the timestamps in the file you give it.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .song import Page
from .timing import format_timestamp

TURN_BEFORE_SINGING = 0.6   # a page should be in place this long before its first sung word
BACK_AFTER_SINGING = 1.5


class SuggestError(RuntimeError):
    pass


@dataclass
class Word:
    text: str
    start: float
    end: float
    probability: float = 1.0


def _norm(text: str) -> str:
    return re.sub(r"[^0-9a-z]", "", text.lower())


def page_spans(pages: list[Page], words: list[Word]) -> dict[int, tuple[float, float]]:
    """First word start and last word end for each page with lines, keyed by page index.

    Matching is by position in the normalized letter stream, so differences in how the
    aligner splits words or punctuation do not shift pages.
    """
    bounds = []          # (page index, first char, last char) in the lyric letter stream
    pos = 0
    for i, p in enumerate(pages):
        n = len(_norm(" ".join(p.lines)))
        if n:
            bounds.append((i, pos, pos + n - 1))
            pos += n
    spans: dict[int, tuple[float, float]] = {}
    cursor = 0
    word_at = []         # (char start, char end, word)
    for w in words:
        n = len(_norm(w.text))
        if n:
            word_at.append((cursor, cursor + n - 1, w))
            cursor += n
    for i, first, last in bounds:
        starts = [w.start for a, b, w in word_at if b >= first and a <= last]
        ends = [w.end for a, b, w in word_at if b >= first and a <= last]
        if starts:
            spans[i] = (min(starts), max(ends))
    return spans


def suggest_turns(pages: list[Page], words: list[Word], duration: float) -> list[float]:
    """One suggested timestamp per page after the first."""
    spans = page_spans(pages, words)
    known: list[float | None] = [None] * len(pages)
    known[0] = 0.0
    for i, p in enumerate(pages[1:], start=1):
        if i in spans:
            known[i] = max(0.1, spans[i][0] - TURN_BEFORE_SINGING)
        elif p.kind == "back" and spans:
            known[i] = min(max(e for _, e in spans.values()) + BACK_AFTER_SINGING, duration - 1.0)
    # Pages with nothing sung on them share the gap between the singing before and the next known page.
    i = 1
    while i < len(pages):
        if known[i] is not None:
            i += 1
            continue
        j = i
        while j < len(pages) and known[j] is None:
            j += 1
        sung_before = [spans[k][1] for k in range(i) if k in spans]
        left = max(sung_before[-1] if sung_before else 0.0, known[i - 1])
        right = known[j] if j < len(pages) else duration - 1.0
        for n, k in enumerate(range(i, j), start=1):
            known[k] = left + (right - left) * n / (j - i + 1)
        i = j
    turns = [round(t, 1) for t in known[1:]]
    for k in range(1, len(turns)):       # keep them strictly increasing
        turns[k] = max(turns[k], round(turns[k - 1] + 0.1, 1))
    return turns


def confidence_note(words: list[Word]) -> str:
    if not words:
        return "Confidence: none. The aligner found no words; set every timestamp by ear."
    probs = [w.probability for w in words]
    mean = sum(probs) / len(probs)
    weak = sum(1 for p in probs if p < 0.3)
    level = "high" if mean >= 0.75 and weak / len(probs) < 0.1 else "medium" if mean >= 0.5 else "low"
    return (f"Confidence: {level} (mean word probability {mean:.2f}, {weak} of {len(probs)} words below 0.30). "
            f"Check every timestamp by ear or with contact-sheet before rendering.")


def separate_vocals(audio: Path, workdir: Path) -> Path:
    try:
        import demucs  # noqa: F401
    except ImportError:
        raise SuggestError("--separate-vocals needs Demucs: pip install -r requirements-align.txt") from None
    cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", str(workdir), str(audio)]
    print("Separating vocals with Demucs (this can take a few minutes)...", file=sys.stderr)
    if subprocess.run(cmd).returncode != 0:
        raise SuggestError("Demucs failed; try again without --separate-vocals.")
    found = list(workdir.glob("htdemucs/*/vocals.wav"))
    if not found:
        raise SuggestError("Demucs finished but no vocals.wav was written.")
    return found[0]


def align_words(audio: Path, pages: list[Page], model_name: str = "base", language: str = "en",
                vocals: bool = False) -> list[Word]:
    try:
        import stable_whisper
    except ImportError:
        raise SuggestError("suggest-timing needs stable-ts, which is not installed. Run:\n"
                           "  pip install -r requirements-align.txt\n"
                           "It runs locally, but the first run downloads the Whisper model.") from None
    text = "\n".join(line for p in pages for line in p.lines)
    with tempfile.TemporaryDirectory() as tmp:
        source = separate_vocals(audio, Path(tmp)) if vocals else audio
        model = stable_whisper.load_model(model_name)
        result = model.align(str(source), text, language=language)
    words = []
    for seg in result.segments:
        for w in seg.words or []:
            words.append(Word(w.word, float(w.start), float(w.end), float(getattr(w, "probability", 1.0) or 0.0)))
    return words


def suggestion_header(model_name: str, vocals: bool, note: str) -> str:
    how = f"stable-ts model {model_name}" + (" on Demucs-separated vocals" if vocals else "")
    return (f"# Suggested by b2s-video suggest-timing ({how}).\n"
            f"# {note}\n"
            f"# These are a starting point only. Edit any line; render uses exactly what this file says.\n")


def describe(pages: list[Page], turns: list[float]) -> str:
    return "\n".join(f"  Page {p.number:<3} {p.label:<13} {format_timestamp(t)}" for p, t in zip(pages[1:], turns))
