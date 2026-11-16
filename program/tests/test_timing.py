import json

import pytest

from b2s_video.song import build_pages, load_song
from b2s_video.timing import TimingError, count_error, format_timestamp, line_times, load_turns_file, \
    parse_inline, parse_timestamp, timing_template, validate_turns

from .conftest import DATA

SAMPLE_TURNS = ["0:03", "0:10", "0:17", "0:24", "0:31", "0:38", "0:45", "0:52", "0:58"]


@pytest.fixture
def pages():
    return build_pages(load_song(DATA / "hand-in-hand.json"))


@pytest.mark.parametrize("text,seconds", [
    ("0:03", 3), ("00:10", 10), ("1:05", 65), ("1:05.5", 65.5), ("01:05.25", 65.25), ("12:00", 720),
    ("75:30", 4530), ("1:02:03", 3723), ("1:02:03.5", 3723.5), ("74.5", 74.5), ("74", 74), ("0", 0),
    (".5", 0.5), ("  0:07 ", 7), (74.5, 74.5), (3, 3),
])
def test_parse_timestamp_formats(text, seconds):
    assert parse_timestamp(text) == pytest.approx(seconds)


@pytest.mark.parametrize("bad,match", [
    ("1:75", "00-59"), ("1:5", "two digits"), ("abc", "m:ss"), ("", "m:ss"), ("-3", "negative"),
    ("1::2", "m:ss"), ("1:02:75", "00-59"), ("1:60:00", "00-59"), ("1,5", "m:ss"), ("0:03s", "m:ss"),
    (-1, "zero or more"), (True, "m:ss"), (None, "m:ss"), (float("nan"), "zero or more"),
])
def test_parse_timestamp_rejects(bad, match):
    with pytest.raises(TimingError, match=match):
        parse_timestamp(bad)


def test_format_timestamp():
    assert format_timestamp(3) == "0:03"
    assert format_timestamp(65.5) == "1:05.5"
    assert format_timestamp(3723) == "1:02:03"
    assert format_timestamp(59.96) == "1:00"


def test_inline_split():
    assert parse_inline("0:03,0:10, 0:17 ,") == ["0:03", "0:10", "0:17"]
    assert parse_inline("3 10.5\t17") == ["3", "10.5", "17"]


def test_text_file(tmp_path):
    f = tmp_path / "turns.txt"
    f.write_text("# a comment\n\n0:03\n  0:10   # inline comment\n\n# page 4\n1:05.5\n", encoding="utf-8")
    assert load_turns_file(f) == (["0:03", "0:10", "1:05.5"], None)


def test_json_file(tmp_path):
    f = tmp_path / "turns.json"
    f.write_text(json.dumps({"turns": ["0:03", 10, 17.5]}), encoding="utf-8")
    assert load_turns_file(f) == (["0:03", 10, 17.5], None)
    f.write_text(json.dumps([3, 10]), encoding="utf-8")
    assert load_turns_file(f) == ([3, 10], None)
    f.write_text(json.dumps({"turns": [3], "lines": {"2": ["0:03.5"]}}), encoding="utf-8")
    assert load_turns_file(f) == ([3], {"2": ["0:03.5"]})
    f.write_text(json.dumps({"times": [3]}), encoding="utf-8")
    with pytest.raises(TimingError, match="turns"):
        load_turns_file(f)


def test_prototype_example_file_still_loads():
    turns, _ = load_turns_file(DATA.parent.parent / "reference" / "turns.example.json")
    assert turns == [3, 10, 17, 24, 31, 38, 45, 52, 58]


def test_all_formats_are_equivalent(tmp_path, pages):
    txt = tmp_path / "t.txt"
    txt.write_text("\n".join(SAMPLE_TURNS), encoding="utf-8")
    js = tmp_path / "t.json"
    js.write_text(json.dumps({"turns": [3, 10, 17, 24, 31, 38, 45, 52, 58]}), encoding="utf-8")
    a = validate_turns(pages, parse_inline(",".join(SAMPLE_TURNS)), 122.1)
    b = validate_turns(pages, load_turns_file(txt)[0], 122.1)
    c = validate_turns(pages, load_turns_file(js)[0], 122.1)
    assert a == b == c
    assert a[0] == [0, 3, 10, 17, 24, 31, 38, 45, 52, 58]


def test_count_check_lists_every_page(pages):
    with pytest.raises(TimingError) as e:
        validate_turns(pages, SAMPLE_TURNS[:-1], 122.1)
    msg = str(e.value)
    assert msg.startswith("9 timestamps expected, got 8.")
    assert 'Page 2   Verse         "Two little kids in the big green wood,"' in msg
    assert 'Page 3   Chorus        "Hand in hand, hand in hand,"' in msg
    for n in range(2, 11):
        assert f"Page {n} " in msg
    assert "Page 10  Back cover" in msg and "missing" in msg
    assert "Page 1 " not in msg.split("The timestamps map")[1]


def test_count_check_too_many(pages):
    msg = count_error(pages, SAMPLE_TURNS + ["2:00"])
    assert msg.startswith("9 timestamps expected, got 10.") and "2:00 (extra)" in msg


def test_count_for_other_page_settings():
    song = load_song(DATA / "hand-in-hand.json")
    assert len(build_pages(song, cover=False, back=False)) - 1 == 7
    with pytest.raises(TimingError, match="7 timestamps expected, got 9"):
        validate_turns(build_pages(song, cover=False, back=False), SAMPLE_TURNS, 122.1)


def test_must_increase_and_fit_audio(pages):
    bad = list(SAMPLE_TURNS)
    bad[3] = "0:15"
    with pytest.raises(TimingError, match="Page 5 \\(Chorus\\) at 0:15 is not after page 4 \\(Verse\\) at 0:17"):
        validate_turns(pages, bad, 122.1)
    with pytest.raises(TimingError, match="after the end of the audio"):
        validate_turns(pages, SAMPLE_TURNS, 50)
    with pytest.raises(TimingError, match="later than 0:00"):
        validate_turns(pages, ["0:00"] + SAMPLE_TURNS[1:], 122.1)
    with pytest.raises(TimingError, match="placeholders"):
        validate_turns(pages, ["00:00"] * 9, 122.1)


def test_bad_value_names_the_page(pages):
    bad = list(SAMPLE_TURNS)
    bad[1] = "zero"
    with pytest.raises(TimingError, match="Page 3 \\(Chorus\\): Bad timestamp \"zero\""):
        validate_turns(pages, bad, 122.1)


def test_warnings_short_page_and_near_end(pages):
    turns = ["0:03", "0:04", "0:17", "0:24", "0:31", "0:38", "0:45", "0:52", "121.5"]
    starts, warnings = validate_turns(pages, turns, 122.1)
    assert any("Page 2 (Verse) is on screen for only 1.0 s" in w for w in warnings)
    assert any("Page 10 (Back cover) at 2:01.5 is within 1 s of the end" in w for w in warnings)
    assert any("Page 10 (Back cover) is on screen for only 0.6 s" in w for w in warnings)


def test_line_timing_even(pages):
    starts, _ = validate_turns(pages, SAMPLE_TURNS, 122.1)
    lt = line_times(pages, starts, 122.1, "even")
    assert lt[0] == [] and lt[-1] == []
    verse = lt[1]                  # page 2 runs 3 to 10 s with 4 lines
    assert verse[0][0] == pytest.approx(3.4)
    assert verse[-1][1] == pytest.approx(10 - 0.8)
    assert all(b[0] == pytest.approx(a[1]) for a, b in zip(verse, verse[1:]))


def test_line_timing_all_and_custom(pages):
    starts, _ = validate_turns(pages, SAMPLE_TURNS, 122.1)
    lt = line_times(pages, starts, 122.1, "all", {"3": ["0:10.5", "0:12", "0:14", "0:15.5"]})
    assert lt[1] is None
    assert lt[2] == [[10.5, 12], [12, 14], [14, 15.5], [15.5, 17]]
    with pytest.raises(TimingError, match="has 4 lines, got 2"):
        line_times(pages, starts, 122.1, "even", {"3": ["0:10.5", "0:12"]})
    with pytest.raises(TimingError, match="within the page"):
        line_times(pages, starts, 122.1, "even", {"3": ["0:09", "0:12", "0:14", "0:15"]})
    with pytest.raises(TimingError, match="no page 42"):
        line_times(pages, starts, 122.1, "even", {"42": []})


def test_init_template_roundtrip(tmp_path, pages):
    text = timing_template(pages, "Hand in Hand")
    assert '# page 2: Verse - "Two little kids in the big green wood,"\n00:00' in text
    assert "# page 10: Back cover\n00:00" in text
    assert text.count("\n00:00") == 9
    filled = text
    for t in SAMPLE_TURNS:
        filled = filled.replace("\n00:00", "\n" + t, 1)
    f = tmp_path / "turns.txt"
    f.write_text(filled, encoding="utf-8")
    values, _ = load_turns_file(f)
    assert values == SAMPLE_TURNS
    validate_turns(pages, values, 122.1)


def test_empty_section_in_template():
    pages = build_pages(load_song(DATA / "lantern.json"))
    text = timing_template(pages, "x")
    assert "# page 2: Intro - (no lines)" in text
    assert "# page 6: Instrumental - (no lines)" in text
