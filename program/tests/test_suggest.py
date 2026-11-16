from b2s_video.song import build_pages, load_song
from b2s_video.suggest import Word, confidence_note, page_spans, suggest_turns

from .conftest import DATA


def _words_for(pages, start=5.0, gap=0.5, page_gap=4.0):
    """Fake aligner output: every lyric word in order, with a pause between pages."""
    words, t = [], start
    for p in pages:
        for line in p.lines:
            for w in line.split():
                words.append(Word(w, t, t + gap * 0.8, 0.9))
                t += gap
        if p.lines:
            t += page_gap
    return words


def test_pages_map_to_first_words():
    pages = build_pages(load_song(DATA / "hand-in-hand.json"))
    words = _words_for(pages)
    spans = page_spans(pages, words)
    assert spans[1][0] == 5.0                     # page 2 starts with the first word
    turns = suggest_turns(pages, words, 200.0)
    assert len(turns) == len(pages) - 1
    assert turns[0] == round(5.0 - 0.6, 1)
    assert all(b > a for a, b in zip(turns, turns[1:]))
    assert turns[-1] > spans[8][1]                # back cover after the last sung word


def test_word_splitting_differences_do_not_shift_pages():
    pages = build_pages(load_song(DATA / "hand-in-hand.json"))
    words = _words_for(pages)
    # the aligner glues punctuation and splits "we're" differently
    merged = []
    for w in words:
        if w.text.startswith("we're"):
            merged += [Word("we", w.start, w.start + 0.1, 0.9), Word("'re", w.start + 0.1, w.end, 0.9)]
        else:
            merged.append(w)
    assert page_spans(pages, merged) == page_spans(pages, words)


def test_empty_pages_get_spread_between_neighbours():
    pages = build_pages(load_song(DATA / "lantern.json"))
    words = _words_for(pages, start=8.0)
    turns = suggest_turns(pages, words, 120.0)
    assert len(turns) == 9
    assert 0 < turns[0] < turns[1]               # [Intro] before the first verse
    assert all(b > a for a, b in zip(turns, turns[1:]))


def test_confidence_note():
    assert "high" in confidence_note([Word("a", 0, 1, 0.95)] * 10)
    assert "low" in confidence_note([Word("a", 0, 1, 0.2)] * 10)
    assert "none" in confidence_note([])
