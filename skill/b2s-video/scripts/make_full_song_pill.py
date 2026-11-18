"""Draw the Short's "Watch the full song" pill as a transparent 1080x1920 PNG.

The Short overlays this image for its last 3 seconds (step 5 of the skill). The pill sits in the
green space below the notebook, centred, clear of YouTube's buttons on the right and its title,
channel and Related video link at the bottom. It has no arrow and no "tap", so it reads the same
on phones and on desktop; the gold play icon matches the play icon on YouTube's Related video link.

Run with the program's venv (it needs Playwright):
  "<program>/.venv/Scripts/python.exe" make_full_song_pill.py --fonts "<program>/b2s_video/assets/fonts" --out "<program>/b2s_video/assets/full-song-pill.png"
"""
import argparse
import asyncio
import base64
import pathlib

from playwright.async_api import async_playwright

TEXT = "Watch the full song"
TOP = 1470          # px from the top of the 1080x1920 frame (the notebook ends at about 1420)


def html(font: pathlib.Path) -> str:
    fredoka = base64.b64encode(font.read_bytes()).decode()
    return f"""<!doctype html><style>
@font-face{{font-family:Fre;src:url(data:font/ttf;base64,{fredoka});font-weight:300 700}}
html,body{{margin:0;width:1080px;height:1920px;background:transparent}}
.wrap{{position:absolute;left:0;right:0;top:{TOP}px;text-align:center}}
.pill{{display:inline-flex;align-items:center;gap:18px;padding:20px 36px 20px 24px;background:#5e2a6e;color:#fff8ec;
  border:4px solid #f3d27a;border-radius:60px;font:600 50px Fre;box-shadow:0 8px 22px rgba(0,0,0,.45)}}
.play{{width:56px;height:56px;border-radius:50%;background:#f3d27a;display:grid;place-items:center}}
</style><div class="wrap"><span class="pill"><span class="play"><svg width="26" height="28" viewBox="0 0 26 28">
<path d="M3 2 L24 14 L3 26 Z" fill="#5e2a6e"/></svg></span>{TEXT}</span></div>"""


async def main(fonts: pathlib.Path, out: pathlib.Path) -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        await page.set_content(html(fonts / "Fredoka-Variable.ttf"))
        await page.evaluate("document.fonts.ready")
        await page.wait_for_timeout(300)
        await page.screenshot(path=str(out), omit_background=True)
        await browser.close()
    print(f"Saved {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fonts", required=True, type=pathlib.Path, help="the program's assets/fonts folder")
    ap.add_argument("--out", required=True, type=pathlib.Path, help="PNG to write")
    a = ap.parse_args()
    asyncio.run(main(a.fonts, a.out))
