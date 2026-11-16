import json

import pytest

from b2s_video.song import SongError, cover_work, build_pages, default_look, load_song, parse_sections, song_title, \
    source_field, typographic, unknown_tags

from .conftest import DATA


def test_sections_and_pages_for_sample():
    song = load_song(DATA / "hand-in-hand.json")
    pages = build_pages(song)
    assert [p.label for p in pages] == ["Cover", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Verse",
                                        "Chorus", "Outro", "Back cover"]
    assert [p.number for p in pages] == list(range(1, 11))
    assert pages[1].first_line == "Two little kids in the big green wood,"
    assert all(len(p.lines) == 4 for p in pages[1:8])
    assert len(pages[8].lines) == 2
    assert [p.repeated for p in pages] == [False, False, True, False, True, False, False, True, False, False]


def test_cover_flags():
    song = load_song(DATA / "hand-in-hand.json")
    assert len(build_pages(song, cover=False)) == 9
    assert len(build_pages(song, back=False)) == 9
    pages = build_pages(song, cover=False, back=False)
    assert pages[0].label == "Verse" and pages[0].number == 1 and len(pages) == 8


def test_empty_sections_become_pages_without_lines():
    secs = parse_sections(["[Intro]", "", "[Verse]", "a", "b", "", "[Instrumental]", "", "[Outro]", "c"])
    assert [(s.tag, s.lines) for s in secs] == [("Intro", []), ("Verse", ["a", "b"]), ("Instrumental", []),
                                               ("Outro", ["c"])]


def test_untagged_lines_and_extra_blanks():
    secs = parse_sections(["first", "", "", "[Verse]", "a", "", "loose"])
    assert [(s.tag, s.lines) for s in secs] == [(None, ["first"]), ("Verse", ["a"]), (None, ["loose"])]


def test_tag_with_spaces_and_numbers():
    secs = parse_sections([" [ Verse 2 ] ", "a"])
    assert secs[0].tag == "Verse 2"


def test_unknown_tag_is_accepted_and_reported():
    secs = parse_sections(["[Spoken Word]", "hi", "", "[Verse 2]", "a", "", "[Final Chorus]", "b", "", "[Hook x2]", "c"])
    assert [s.tag for s in secs] == ["Spoken Word", "Verse 2", "Final Chorus", "Hook x2"]
    assert unknown_tags(secs) == ["Spoken Word"]


@pytest.mark.parametrize("tag,repeated", [("Chorus", True), ("chorus", True), ("Hook", True), ("Chorus 2", True),
                                          ("Final Chorus", True), ("Pre-chorus", False), ("Post-chorus", False),
                                          ("Verse", False), ("Bridge", False)])
def test_repeated_styling(tag, repeated):
    song = {"lyrics": [f"[{tag}]", "a line"]}
    assert build_pages(song, cover=False, back=False)[0].repeated is repeated


def test_missing_optional_fields(tmp_path):
    path = tmp_path / "my-little-song.json"
    path.write_text(json.dumps({"lyrics": ["[Verse]", "a"]}), encoding="utf-8")
    song = load_song(path)
    assert song_title(song) == "My Little Song"
    assert source_field(song, "work") is None and source_field(song, "author") is None
    assert default_look(song) == "notebook"
    assert len(build_pages(song)) == 3


def test_source_not_a_dict():
    assert source_field({"source": "Grimm"}, "work") is None
    assert source_field({"source": {"work": "  "}}, "work") is None


def test_notebook_is_the_default_look():
    assert default_look({"channel": "general"}) == "notebook"
    assert default_look({"channel": "kids"}) == "notebook"


def test_bad_songs(tmp_path):
    with pytest.raises(SongError, match="not found"):
        load_song(tmp_path / "nope.json")
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    with pytest.raises(SongError, match="not valid JSON"):
        load_song(tmp_path / "bad.json")
    (tmp_path / "nolyrics.json").write_text('{"title": "x"}', encoding="utf-8")
    with pytest.raises(SongError, match="lyrics"):
        load_song(tmp_path / "nolyrics.json")
    with pytest.raises(SongError, match="nothing to put"):
        build_pages({"lyrics": ["", ""]})
    with pytest.raises(SongError, match="expected a string"):
        build_pages({"lyrics": ["[Verse]", 3]})


def test_typographic_apostrophes_only():
    assert typographic("Together we're strong, it's 'right'") == "Together we’re strong, it’s ’right’"
    assert typographic('No "quotes" changed') == 'No "quotes" changed'


def test_three_songs_have_different_shapes():
    shapes = {}
    for name in ("hand-in-hand", "lantern", "long-road"):
        pages = build_pages(load_song(DATA / f"{name}.json"))
        shapes[name] = [(p.label, len(p.lines)) for p in pages]
    assert shapes["lantern"] == [("Cover", 0), ("Intro", 0), ("Verse", 2), ("Pre-chorus", 1), ("Hook", 2),
                                 ("Instrumental", 0), ("Verse", 2), ("Hook", 2), ("Breakdown", 1), ("Back cover", 0)]
    assert shapes["long-road"] == [("Cover", 0), ("Verse", 8), ("Chorus", 1), ("Spoken Word", 1), ("Outro", 1),
                                   ("Back cover", 0)]
    assert len(shapes["hand-in-hand"]) == 10


def _two_versions(tmp_path):
    path = tmp_path / "multi.json"
    path.write_text(json.dumps({
        "source": {"work": "Beauty and the Beast", "author": "Beaumont"},
        "versions": [
            {"channel": "kids", "title": "True Beauty", "lyrics": ["[Verse]", "kids line"]},
            {"channel": "general", "title": "A Rose in the Snow", "lyrics": ["[Verse]", "general line", "", "[Chorus]", "c"]},
        ]}), encoding="utf-8")
    return path


def test_versions_picked_by_audio_name(tmp_path):
    song = load_song(_two_versions(tmp_path), audio="C:/x/A+Rose+in+the+Snow.mp3")
    assert song_title(song) == "A Rose in the Snow"
    assert source_field(song, "work") == "Beauty and the Beast"     # shared fields kept
    assert default_look(song) == "notebook"
    assert [p.label for p in build_pages(song)] == ["Cover", "Verse", "Chorus", "Back cover"]


@pytest.mark.parametrize("choice,title", [("1", "True Beauty"), ("kids", "True Beauty"), ("General", "A Rose in the Snow"),
                                          ("true beauty", "True Beauty")])
def test_versions_picked_by_choice(tmp_path, choice, title):
    assert song_title(load_song(_two_versions(tmp_path), version=choice, audio="other.mp3")) == title


def test_versions_need_a_choice(tmp_path):
    with pytest.raises(SongError, match="2 versions.*--version") as e:
        load_song(_two_versions(tmp_path), audio="song.mp3")
    assert "1. True Beauty (kids)" in str(e.value) and "2. A Rose in the Snow (general)" in str(e.value)
    with pytest.raises(SongError, match="matches no single version"):
        load_song(_two_versions(tmp_path), version="3")
    with pytest.raises(SongError, match="no \"versions\""):
        load_song(DATA / "hand-in-hand.json", version="1")


def test_cover_drops_a_bracketed_note():
    assert cover_work("The sinking of RMS Titanic (historical event, April 1912)") == "The sinking of RMS Titanic"
    assert cover_work("Romeo and Juliet") == "Romeo and Juliet"
    assert cover_work("Tales (1812) of Grimm") == "Tales (1812) of Grimm"     # only a note at the very end
    assert cover_work("(untitled)") == "(untitled)"                           # never left empty
