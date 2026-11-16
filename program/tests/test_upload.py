import json

import pytest

from b2s_video import cli
from b2s_video.song import SongError
from b2s_video.upload import from_flat, keep_filled, pick_version, tag_chars, upload_text

YT = {
    "normal": {
        "title": "Pay the Piper | Pied Piper of Hamelin Song",
        "description": ["A song about keeping your word.", "", "Watch the Short: {SHORT_URL}"],
        "tags": ["pied piper", "hamelin"],
        "thumbnail_text": "PAY THE PIPER",
        "studio_settings": {"made_for_kids": "No", "altered_or_synthetic": "Yes"},
    },
    "short": {"title": "Pay the Piper #shorts", "description": "Full song: {FULL_VIDEO_URL}"},
    "pinned_comment": "Which promise would you keep?",
}


def song(*versions):
    return {"plot_summary": ["..."], "versions": list(versions)}


def write(tmp_path, data, folder="pay-the-piper", name="pay-the-piper.json"):
    d = tmp_path / folder
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_text_has_both_parts_and_counts():
    text = upload_text({"title": "Pay the Piper", "youtube": YT}, "pay-the-piper.json", "pay-the-piper")
    assert text.startswith('YouTube upload text for "Pay the Piper"\n')
    assert "REGULAR VIDEO   (pay-the-piper-16x9.mp4 + pay-the-piper-thumbnail.jpg)" in text
    assert "SHORT   (pay-the-piper-short-*.mp4 + pay-the-piper-thumbnail-9x16.jpg)" in text
    assert "--- TITLE ---  (42/100)\nPay the Piper | Pied Piper of Hamelin Song\n" in text
    assert "A song about keeping your word.\n\nWatch the Short" in text      # list of lines joined
    assert "--- TAGS (paste into the Tags box) ---  (20/500)\npied piper, hamelin\n" in text
    assert "Made for kids: No" in text
    assert text.count("Which promise would you keep?") == 2               # shared field used by both parts
    assert '"' not in text.split("\n", 1)[1]                               # no JSON quotes after the heading


def test_tag_chars_counts_quotes_and_commas():
    assert tag_chars(["a b", "c"]) == 3 + 2 + 1 + 1
    assert tag_chars([]) == 0


def test_flat_layout_lists_title_options():
    yt = from_flat({"titles": ["One", "Two"], "description": "D", "tags": ["t"], "shorts_title": "S",
                    "made_for_kids": False})
    assert yt["normal"]["title"] == "One   [3/100]\nTwo   [3/100]"
    assert yt["short"]["title"] == "S" and yt["short"]["studio_settings"] == {"made_for_kids": False}
    text = upload_text({"title": "X", "youtube": {"titles": ["One", "Two"], "description": "D"}}, "x.json", "x")
    assert "--- TITLE OPTIONS (pick one) ---" in text


def test_pick_version():
    a = {"title": "A", "channel": "kids", "lyrics": []}
    b = {"title": "B", "channel": "general", "lyrics": [], "youtube": YT}
    assert pick_version(song(a, b))["title"] == "B"
    assert pick_version(song(a, b), "general")["title"] == "B"
    with pytest.raises(SongError, match="no \"youtube\" block"):
        pick_version(song(a, b), "1")
    with pytest.raises(SongError, match="video-upload-metadata"):
        pick_version(song(a))
    with pytest.raises(SongError, match="pass --version"):
        pick_version(song(b, dict(b, title="C")))
    assert pick_version({"title": "Solo", "youtube": YT})["title"] == "Solo"


def test_command_writes_default_out_and_lists_placeholders(tmp_path, capsys):
    p = write(tmp_path, song({"title": "Pay the Piper", "lyrics": [], "youtube": YT}))
    assert cli.main(["upload-text", "--song", str(p)]) == 0
    out = tmp_path / "pay-the-piper" / "out" / "pay-the-piper-youtube.txt"
    assert out.read_text(encoding="utf-8").startswith("YouTube upload text for")
    printed = capsys.readouterr().out
    assert "Placeholders still to fill in: {FULL_VIDEO_URL}, {SHORT_URL}" in printed
    assert cli.main(["upload-text", "--song", str(p)]) == 0               # replaces its own file


def test_keep_filled_carries_hand_edits():
    new = "Title\nFull song: {FULL_VIDEO_URL}\nShort: {SHORT_URL} and {FULL_VIDEO_URL}\nUntouched: {X_URL}"
    old = "Old title\nFull song: https://youtu.be/abc\nShort: https://youtu.be/s and https://youtu.be/abc\nUntouched: {X_URL}"
    text, kept = keep_filled(old, new)
    assert text == ("Title\nFull song: https://youtu.be/abc\nShort: https://youtu.be/s and https://youtu.be/abc\n"
                    "Untouched: {X_URL}")
    assert sorted(set(kept)) == ["{FULL_VIDEO_URL}", "{SHORT_URL}"]
    assert keep_filled("nothing alike", new) == (new, [])


def test_command_keeps_filled_link_when_remade(tmp_path, capsys):
    p = write(tmp_path, song({"title": "Pay the Piper", "lyrics": [], "youtube": YT}))
    cli.main(["upload-text", "--song", str(p)])
    out = tmp_path / "pay-the-piper" / "out" / "pay-the-piper-youtube.txt"
    out.write_text(out.read_text(encoding="utf-8").replace("{FULL_VIDEO_URL}", "https://youtu.be/abc"), encoding="utf-8")
    capsys.readouterr()
    assert cli.main(["upload-text", "--song", str(p)]) == 0
    assert "Full song: https://youtu.be/abc" in out.read_text(encoding="utf-8")
    printed = capsys.readouterr().out
    assert "Kept what you filled in by hand for: {FULL_VIDEO_URL}" in printed
    assert "Placeholders still to fill in: {SHORT_URL}" in printed


def test_command_keeps_other_files_unless_forced(tmp_path, capsys):
    p = write(tmp_path, song({"title": "Pay the Piper", "lyrics": [], "youtube": YT}))
    other = tmp_path / "notes.txt"
    other.write_text("my own notes\n", encoding="utf-8")
    assert cli.main(["upload-text", "--song", str(p), "--out", str(other)]) == 2
    assert "--force" in capsys.readouterr().err
    assert other.read_text(encoding="utf-8") == "my own notes\n"
    assert cli.main(["upload-text", "--song", str(p), "--out", str(other), "--force"]) == 0


def test_command_without_youtube_block(tmp_path, capsys):
    p = write(tmp_path, song({"title": "Pay the Piper", "lyrics": []}))
    assert cli.main(["upload-text", "--song", str(p)]) == 2
    assert "video-upload-metadata" in capsys.readouterr().err
