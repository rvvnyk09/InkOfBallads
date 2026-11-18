"""Browser and ffmpeg tests. They skip when Chromium or ffmpeg is not installed."""
import asyncio
import base64
import json
import re
import struct

import pytest

from b2s_video import cli
from b2s_video.render import TEMPLATES, Job, _jpeg_frame, _launch, _open, check_layout, probe_streams, render_stills
from b2s_video.song import build_pages, load_song, song_title, source_field
from b2s_video.timing import line_times, validate_turns

from .conftest import DATA, needs_browser, needs_ffmpeg

SONGS = {
    "hand-in-hand": ["0:03", "0:10", "0:17", "0:24", "0:31", "0:38", "0:45", "0:52", "0:58"],
    "lantern": ["0:02", "0:05", "0:09", "0:12", "0:18", "0:21", "0:26", "0:31", "0:36"],
    "long-road": ["0:02", "0:20", "0:30", "0:34", "0:38"],
}


def make_job(name, fmt="16x9", total=65.0, mode="even", look=None):
    song = load_song(DATA / f"{name}.json")
    pages = build_pages(song)
    starts, _ = validate_turns(pages, SONGS[name], total)
    return Job(pages, starts, line_times(pages, starts, total, mode), format=fmt,
               look=look or ("classic" if song.get("channel") == "general" else "kids"),
               title=song_title(song), work=source_field(song, "work"), author=source_field(song, "author"),
               channel="Test Channel", total=total)


def png_size(data: bytes):
    return struct.unpack(">II", data[16:24])


@pytest.mark.parametrize("template", sorted(set(TEMPLATES.values())), ids=lambda p: p.name)
def test_template_loads_nothing_from_the_internet(template):
    html = template.read_text(encoding="utf-8")
    assert not re.search(r"https?://", html)
    assert "transition:none" in html and "setTimeout" not in html and "setInterval" not in html


@needs_browser
@pytest.mark.parametrize("name", list(SONGS))
@pytest.mark.parametrize("fmt", ["16x9", "9x16"])
@pytest.mark.parametrize("look", [None, "notebook"])
def test_every_page_fits(name, fmt, look):
    info = check_layout(make_job(name, fmt, look=look))
    assert info.overflow == [], f"pages that overflow: {info.overflow}"


@needs_browser
@pytest.mark.parametrize("fmt", ["16x9", "9x16"])
def test_subscribe_fits_on_the_end_page(fmt):
    job = make_job("hand-in-hand", fmt, look="notebook")
    job.subscribe = True
    assert job.config()["subscribe"] is True
    info = check_layout(job)
    assert info.overflow == [], f"pages that overflow: {info.overflow}"
    assert info.k[-1] == 1, "the End page shrank to make room"


@needs_browser
@pytest.mark.parametrize("look", [None, "notebook"])
def test_long_pages_shrink(look):
    job = make_job("long-road", look=look)
    if look == "notebook":               # the notebook's wider lines fit the test word, so make it longer
        job.pages[4].lines = [job.pages[4].lines[0] * 2]
    info = check_layout(job)
    k = info.k
    assert k[1] < 1                      # lyric pages share one smaller size because of the very long line
    assert k[1] == k[2] == k[3]          # 8-line verse, very long line, short page: same size
    assert k[4] < k[1]                   # an unbreakable long word shrinks its own page further


@needs_browser
def test_font_size_changes_the_lyrics_and_still_fits():
    small, big = make_job("hand-in-hand", "9x16", look="notebook"), make_job("hand-in-hand", "9x16", look="notebook")
    big.font_size = 33
    assert big.config()["fontSize"] == 33 and small.config()["fontSize"] is None
    assert check_layout(big).overflow == []
    t = [12.2]                                                  # a lyric page
    assert render_stills(small, t)[0] != render_stills(big, t)[0]


@needs_browser
@pytest.mark.parametrize("fmt,size", [("16x9", (1920, 1080)), ("9x16", (1080, 1920))])
def test_stills_have_the_right_size(fmt, size):
    shots, _ = render_stills(make_job("lantern", fmt), [1.0, 3.0, 19.0])
    assert all(png_size(s) == size for s in shots)


@needs_browser
@pytest.mark.parametrize("look", [None, "notebook"])
def test_frames_are_deterministic(look):
    """The same time gives the same pixels, whatever was drawn before it."""
    job = make_job("hand-in-hand", look=look)

    async def go():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            b1, b2 = await _launch(pw), await _launch(pw)
            try:
                p1, c1, _ = await _open(b1, job)
                p2, c2, _ = await _open(b2, job)
                for t in (40.0, 5.0, 9.9):
                    await _jpeg_frame(p1, c1, t)
                a = await _jpeg_frame(p1, c1, 12.2)
                b = await _jpeg_frame(p2, c2, 12.2)
                mid1 = await _jpeg_frame(p1, c1, 10.1)
                mid2 = await _jpeg_frame(p2, c2, 10.1)
                return a, b, mid1, mid2
            finally:
                await b1.close()
                await b2.close()

    a, b, mid1, mid2 = asyncio.run(go())
    assert a == b
    assert mid1 == mid2
    assert a != mid1


@needs_browser
@needs_ffmpeg
def test_smoke_render(tone, tmp_path):
    out = tmp_path / "smoke.mp4"
    code = cli.main(["render", "--song", str(DATA / "lantern.json"), "--audio", str(tone), "--out", str(out),
                     "--turns", "0:01,1.5,2,2.5,3,3.5,4,4.3,4.6", "--fps", "6", "--workers", "2",
                     "--format", "9x16"])
    assert code == 0
    info = probe_streams(out)
    video = [s for s in info["streams"] if s["codec_type"] == "video"]
    audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
    assert video[0]["codec_name"] == "h264" and video[0]["pix_fmt"] == "yuv420p"
    assert (video[0]["width"], video[0]["height"]) == (1080, 1920)
    assert audio[0]["codec_name"] == "aac"
    assert float(info["format"]["duration"]) == pytest.approx(5.0, abs=0.15)
    assert not (tmp_path / "smoke.mp4.part").exists()


@needs_browser
@needs_ffmpeg
def test_max_seconds_and_still(tone, tmp_path):
    turns = "1,1.5,2,2.5,3,3.5,4,4.3,4.6"
    out = tmp_path / "short.mp4"
    assert cli.main(["--song", str(DATA / "lantern.json"), "--audio", str(tone), "--out", str(out),
                     "--turns", turns, "--fps", "5", "--max-seconds", "2"]) == 0
    assert float(probe_streams(out)["format"]["duration"]) == pytest.approx(2.0, abs=0.15)
    png = tmp_path / "still.png"
    assert cli.main(["--song", str(DATA / "lantern.json"), "--audio", str(tone), "--out", str(png),
                     "--turns", turns, "--still", "2.2"]) == 0
    assert png_size(png.read_bytes()) == (1920, 1080)


@needs_browser
@needs_ffmpeg
def test_contact_sheet(tone, tmp_path):
    out = tmp_path / "sheet.png"
    turns = tmp_path / "t.txt"
    turns.write_text("1\n1.5\n2\n2.5\n3\n3.5\n4\n4.3\n4.6\n", encoding="utf-8")
    assert cli.main(["contact-sheet", "--song", str(DATA / "lantern.json"), "--audio", str(tone),
                     "--turns-file", str(turns), "--out", str(out)]) == 0
    w, h = png_size(out.read_bytes())
    assert w > 1500 and h > 600


@needs_browser
@pytest.mark.parametrize("look", [None, "notebook"])
def test_highlight_is_off_by_default(look):
    job = make_job("hand-in-hand", look=look)
    assert job.highlight is False
    off, _ = render_stills(job, [5.5])              # mid-line on page 2
    job.highlight = True
    on, _ = render_stills(job, [5.5])
    assert off != on


@needs_browser
@pytest.mark.parametrize("look", [None, "notebook"])
def test_section_tags_are_not_shown(look):
    job = make_job("lantern", look=look)

    async def go():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await _launch(pw)
            try:
                page, _, _ = await _open(browser, job)
                return await page.evaluate("document.querySelector('#stage, #scene').textContent")
            finally:
                await browser.close()

    text = asyncio.run(go())
    for tag in ("Intro", "Verse", "Pre-chorus", "Hook", "Instrumental", "Breakdown"):
        assert tag not in text
    assert "On a rock where the grey waves break," in text


@needs_browser
@needs_ffmpeg
@pytest.mark.parametrize("look", ["notebook", "kids"])
def test_preview_page_plays_in_a_browser(tone, tmp_path, look):
    out = tmp_path / "preview.html"
    assert cli.main(["preview", "--song", str(DATA / "lantern.json"), "--audio", str(tone), "--out", str(out),
                     "--turns", "1,1.5,2,2.5,3,3.5,4,4.3,4.6", "--format", "9x16", "--look", look]) == 0
    html = out.read_text(encoding="utf-8")
    assert "assets/fonts" not in html and not re.search(r"https?://", html)   # fonts embedded, nothing online
    src = re.search(r"AUDIO = (\"[^\"]*\")", html).group(1)          # the audio path the page plays

    async def go():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await _launch(pw)
            try:
                page = await browser.new_page(viewport={"width": 600, "height": 900})
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                await page.goto(out.as_uri())
                await page.wait_for_selector("#b2s-bar")
                duration = await page.evaluate("""() => new Promise(r => { const a = new Audio(%s);
                    a.onloadedmetadata = () => r(a.duration); a.onerror = () => r(-1); })""" % src)
                text = await page.evaluate("document.querySelector('#stage, #scene').textContent")
                return errors, duration, text
            finally:
                await browser.close()

    errors, duration, text = asyncio.run(go())
    assert errors == []
    assert duration == pytest.approx(5.0, abs=0.2)     # the audio is found next to the page
    assert "On a rock where the grey waves break," in text


TINY_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


@needs_browser
@pytest.mark.parametrize("fmt", ["16x9", "9x16"])
def test_logo_on_cover_pages_end_and_tabs(fmt):
    job = make_job("lantern", fmt, look="notebook")
    job.logo = job.mark = "data:image/png;base64," + base64.b64encode(TINY_PNG).decode()

    async def go():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await _launch(pw)
            try:
                page, _, info = await _open(browser, job)
                found = await page.evaluate("""() => {
                    const n = s => document.querySelectorAll(s).length;
                    return [n('.cover .cover-logo'), n('.cover .cover-name'), n('.page-section .watermark'),
                            n('.page-back .end-logo'), n('.tab .mark'), n('.tab')]; }""")
                return found, info
            finally:
                await browser.close()

    (cover, name, marks, end, tab_marks, tabs), info = asyncio.run(go())
    sections = sum(p.kind == "section" for p in job.pages)
    assert (cover, name, end) == (1, 0, 1)
    assert marks == sections                  # a watermark behind every lyric page
    assert tab_marks == tabs == len(job.pages) - 1
    assert info.overflow == []                # the End page still fits with the logo on it


@needs_browser
def test_no_logo_keeps_the_plain_notebook():
    async def go():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await _launch(pw)
            try:
                page, _, _ = await _open(browser, make_job("lantern", look="notebook"))
                return await page.evaluate("""() => [document.querySelectorAll('.inked').length,
                    document.querySelector('.page-section .tab').textContent]""")
            finally:
                await browser.close()

    assert asyncio.run(go()) == [0, "♪"]


@needs_browser
@needs_ffmpeg
def test_logo_option_checks_the_file(tone, tmp_path):
    base = ["--song", str(DATA / "lantern.json"), "--audio", str(tone), "--turns", "1,1.5,2,2.5,3,3.5,4,4.3,4.6",
            "--still", "0.5"]
    assert cli.main(base + ["--out", str(tmp_path / "a.png"), "--logo", str(tmp_path / "missing.png")]) == 2
    assert cli.main(base + ["--out", str(tmp_path / "b.png"), "--logo", str(DATA / "lantern.json")]) == 2
    logo = tmp_path / "logo.png"
    logo.write_bytes(TINY_PNG)
    assert cli.main(base + ["--out", str(tmp_path / "c.png"), "--logo", str(logo), "--logo-mark", str(logo)]) == 0
    assert cli.main(base + ["--out", str(tmp_path / "d.png"), "--logo-mark", str(tmp_path / "missing.png")]) == 2
