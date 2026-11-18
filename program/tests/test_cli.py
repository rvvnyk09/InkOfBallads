import pytest

from b2s_video import cli, render

from .conftest import DATA

SONG = str(DATA / "hand-in-hand.json")


@pytest.fixture
def fake_audio(monkeypatch):
    monkeypatch.setattr(render, "probe_duration", lambda path: 122.1)


def test_init_timing_writes_file(tmp_path, capsys):
    out = tmp_path / "turns.txt"
    assert cli.main(["init-timing", "--song", SONG, "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.count("\n00:00") == 9
    assert "9 timestamps to fill in for 10 pages" in capsys.readouterr().out
    assert cli.main(["init-timing", "--song", SONG, "--out", str(out)]) == 2
    assert "already exists" in capsys.readouterr().err


def test_init_timing_respects_cover_flags(tmp_path):
    out = tmp_path / "turns.txt"
    cli.main(["init-timing", "--song", SONG, "--out", str(out), "--no-cover", "--no-back-cover"])
    text = out.read_text(encoding="utf-8")
    assert text.count("\n00:00") == 7
    assert "made with --no-cover --no-back-cover" in text
    assert "# page 1: Verse - shown from 0:00" in text


def test_wrong_count_prints_listing(fake_audio, capsys, tmp_path):
    code = cli.main(["--song", SONG, "--audio", "x.mp3", "--out", str(tmp_path / "o.mp4"),
                     "--turns", "0:03,0:10,0:17,0:24,0:31,0:38,0:45,0:52"])
    err = capsys.readouterr().err
    assert code == 2
    assert "9 timestamps expected, got 8." in err
    assert 'Page 2   Verse         "Two little kids in the big green wood,"' in err
    assert "Page 10  Back cover" in err


def test_both_turn_sources_is_an_error(fake_audio, capsys, tmp_path):
    code = cli.main(["render", "--song", SONG, "--audio", "x.mp3", "--out", str(tmp_path / "o.mp4"),
                     "--turns", "1", "--turns-file", "t.txt"])
    assert code == 2 and "not both" in capsys.readouterr().err


def test_no_turns_suggests_init(fake_audio, capsys, tmp_path):
    code = cli.main(["--song", SONG, "--audio", "x.mp3", "--out", str(tmp_path / "o.mp4")])
    assert code == 2 and "init-timing" in capsys.readouterr().err


def test_still_needs_png(fake_audio, capsys, tmp_path):
    code = cli.main(["--song", SONG, "--audio", "x.mp3", "--out", str(tmp_path / "o.mp4"), "--still", "3",
                     "--turns", "3,10,17,24,31,38,45,52,58"])
    assert code == 2 and ".png" in capsys.readouterr().err


def test_missing_ffmpeg_message(monkeypatch, tmp_path):
    monkeypatch.setattr(render.shutil, "which", lambda name: None)
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"x")
    with pytest.raises(render.RenderError, match="ffprobe was not found on PATH"):
        render.probe_duration(audio)


def test_render_is_default_command():
    args = cli.build_parser().parse_args(["render", "--song", "s", "--audio", "a", "--out", "o.mp4"])
    assert args.command == "render" and args.format == "16x9" and args.line_timing == "all" and args.fps == 30


@pytest.mark.parametrize("command", ["render", "contact-sheet", "preview"])
def test_subscribe_is_on_by_default(command):
    base = [command, "--song", "s", "--audio", "a", "--out", "o"]
    assert cli.build_parser().parse_args(base).subscribe is True
    assert cli.build_parser().parse_args(base + ["--no-subscribe"]).subscribe is False


def test_font_size_option(capsys):
    base = ["render", "--song", "s", "--audio", "a", "--out", "o.mp4"]
    assert cli.build_parser().parse_args(base).font_size is None
    assert cli.build_parser().parse_args(base + ["--font-size", "32"]).font_size == 32
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(base + ["--font-size", "0"])
    assert "must be more than 0" in capsys.readouterr().err
