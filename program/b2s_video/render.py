"""Draw frames with headless Chromium and encode them with ffmpeg."""
from __future__ import annotations

import asyncio
import base64
import json
import math
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .song import Page, cover_work, typographic

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"
NOTEBOOK = HERE / "notebook.html"
# The page each look is drawn with. Every template has the same setup(cfg) and renderAt(t).
TEMPLATES = {"notebook": NOTEBOOK, "kids": TEMPLATE, "classic": TEMPLATE}
SIZES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
JPEG_QUALITY = 92


class RenderError(RuntimeError):
    """A tool is missing or rendering failed."""


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RenderError(
            f"{name} was not found on PATH. Install ffmpeg (it includes ffprobe) and make sure both are on PATH.\n"
            f"  Windows: winget install Gyan.FFmpeg   (then open a new terminal)\n"
            f"  macOS:   brew install ffmpeg\n"
            f"  Linux:   sudo apt install ffmpeg")
    return path


def probe_duration(audio: str | Path) -> float:
    if not Path(audio).is_file():
        raise RenderError(f"Audio file not found: {audio}")
    ffprobe = require_tool("ffprobe")
    proc = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=nw=1:nk=1", str(audio)], capture_output=True, text=True)
    try:
        duration = float(proc.stdout.strip())
    except ValueError:
        raise RenderError(f"ffprobe could not read the length of {audio}: {proc.stderr.strip() or 'unknown error'}") from None
    if duration <= 0:
        raise RenderError(f"{audio} has no audio length.")
    return duration


def probe_streams(path: str | Path) -> dict:
    """Codec and length facts about a rendered file (used by the tests)."""
    ffprobe = require_tool("ffprobe")
    out = subprocess.run([ffprobe, "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


@dataclass
class Job:
    """Everything the page template needs to draw any frame."""
    pages: list[Page]
    starts: list[float]
    lines: list
    format: str = "16x9"
    look: str = "notebook"
    title: str = ""
    work: str | None = None
    author: str | None = None
    channel: str | None = None
    logo: str | None = None      # a data: URI: the notebook cover, a page watermark and The End page
    mark: str | None = None      # a data: URI: the symbol on the notebook's page tabs
    highlight: bool = False      # color the line being sung berry red
    subscribe: bool = False      # "Like & Subscribe" on the notebook's The End page
    total: float = 0.0

    @property
    def size(self) -> tuple[int, int]:
        return SIZES[self.format]

    def config(self) -> dict:
        w, h = self.size
        return {
            "W": w, "H": h, "look": self.look,
            "title": typographic(self.title),
            "work": typographic(cover_work(self.work)) if self.work else None,
            "author": typographic(self.author) if self.author else None,
            "channel": typographic(self.channel) if self.channel else None,
            "logo": self.logo, "mark": self.mark,
            "highlight": self.highlight, "subscribe": self.subscribe,
            "starts": self.starts, "lines": self.lines,
            "pages": [{"kind": p.kind, "tag": typographic(p.tag) if p.tag else None,
                       "lines": [typographic(l) for l in p.lines], "repeated": p.repeated} for p in self.pages],
        }


@dataclass
class SetupInfo:
    k: list[float] = field(default_factory=list)
    overflow: list[int] = field(default_factory=list)


async def _launch(pw):
    from playwright.async_api import Error as PlaywrightError
    try:
        # --disable-partial-raster: redraw changed tiles in full, so a frame never reuses pixels from an
        # earlier one (the notebook's 3D page turn otherwise left tiny differences around the spiral).
        return await pw.chromium.launch(args=["--disable-gpu", "--font-render-hinting=none", "--disable-partial-raster"])
    except PlaywrightError as e:
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
            raise RenderError("Chromium for Playwright is not installed. Run:\n"
                              f"  {Path(sys.executable).name} -m playwright install chromium") from None
        raise RenderError(f"Chromium could not start: {e}") from None


async def _block_network(route):
    if route.request.url.startswith(("file:", "data:", "about:")):
        await route.continue_()
    else:
        await route.abort()


async def _open(browser, job: Job):
    w, h = job.size
    page = await browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    await page.route("**/*", _block_network)
    await page.goto(TEMPLATES[job.look].as_uri())
    info = await page.evaluate("cfg => window.setup(cfg)", job.config())
    if not info["fontsOk"]:
        raise RenderError("The bundled fonts did not load. Reinstall b2s-video (assets/fonts is missing).")
    cdp = await page.context.new_cdp_session(page)
    return page, cdp, SetupInfo(k=info["k"], overflow=info["overflow"])


async def _jpeg_frame(page, cdp, t: float) -> bytes:
    await page.evaluate("t => window.renderAt(t)", t)
    shot = await cdp.send("Page.captureScreenshot",
                          {"format": "jpeg", "quality": JPEG_QUALITY, "optimizeForSpeed": True})
    return base64.b64decode(shot["data"])


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------- stills

async def _stills(job: Job, times: list[float], fmt: str) -> tuple[list[bytes], SetupInfo]:
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await _launch(pw)
        try:
            page, _cdp, info = await _open(browser, job)
            shots = []
            for t in times:
                await page.evaluate("t => window.renderAt(t)", t)
                shots.append(await page.screenshot(type=fmt, **({"quality": 90} if fmt == "jpeg" else {})))
            return shots, info
        finally:
            await browser.close()


def render_stills(job: Job, times: list[float], fmt: str = "png") -> tuple[list[bytes], SetupInfo]:
    return _run(_stills(job, times, fmt))


def render_still(job: Job, t: float, out: str | Path) -> SetupInfo:
    shots, info = render_stills(job, [t], "png")
    Path(out).write_bytes(shots[0])
    return info


def check_layout(job: Job) -> SetupInfo:
    return render_stills(job, [], "png")[1]


# ---------------------------------------------------------------- video

def default_workers() -> int:
    return max(1, min(4, (os.cpu_count() or 2) // 2))


def frame_count(duration: float, fps: int) -> int:
    return max(1, math.ceil(duration * fps - 1e-6))


async def _video(job: Job, audio: str, out: Path, fps: int, duration: float, workers: int, crf: int,
                 progress: Callable[[int, int], None] | None) -> SetupInfo:
    from playwright.async_api import async_playwright
    ffmpeg = require_tool("ffmpeg")
    frames = frame_count(duration, fps)
    tmp = out.with_name(out.name + ".part")
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(fps), "-i", "-",
           "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-t", f"{duration:.3f}",
           # Chromium's JPEGs are full-range BT.601; convert to the limited-range BT.709 yuv420p players expect.
           "-vf", "scale=in_range=full:out_range=limited:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(fps),
           "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4", str(tmp)]
    proc = await asyncio.create_subprocess_exec(*cmd, stdin=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    err_chunks: list[bytes] = []

    async def read_stderr():
        while chunk := await proc.stderr.read(4096):
            err_chunks.append(chunk)

    err_task = asyncio.create_task(read_stderr())
    workers = max(1, min(workers, frames))
    info = SetupInfo()
    try:
        async with async_playwright() as pw:
            browsers = await asyncio.gather(*[_launch(pw) for _ in range(workers)])
            try:
                sessions = await asyncio.gather(*[_open(b, job) for b in browsers])
                info = sessions[0][2]
                # At most this many finished frames wait in memory for the writer.
                window = asyncio.Semaphore(workers * 3)
                ready: dict[int, bytes] = {}
                arrived = asyncio.Condition()
                next_frame = 0

                async def worker(page, cdp):
                    nonlocal next_frame
                    while True:
                        await window.acquire()
                        f = next_frame
                        if f >= frames:
                            window.release()
                            return
                        next_frame += 1
                        data = await _jpeg_frame(page, cdp, f / fps)
                        async with arrived:
                            ready[f] = data
                            arrived.notify_all()

                async def writer():
                    for f in range(frames):
                        async with arrived:
                            await arrived.wait_for(lambda: f in ready)
                            data = ready.pop(f)
                        proc.stdin.write(data)
                        await proc.stdin.drain()
                        window.release()
                        if progress:
                            progress(f + 1, frames)
                    proc.stdin.close()

                tasks = [asyncio.create_task(writer())] + [asyncio.create_task(worker(p, c)) for p, c, _ in sessions]
                try:
                    await asyncio.gather(*tasks)
                except BaseException:
                    for task in tasks:
                        task.cancel()
                    raise
            finally:
                for b in browsers:
                    await b.close()
    except (BrokenPipeError, ConnectionResetError):
        await proc.wait()
        await err_task
        tmp.unlink(missing_ok=True)
        raise RenderError("ffmpeg stopped early:\n" + b"".join(err_chunks).decode(errors="replace")) from None
    except BaseException:
        if proc.returncode is None:
            proc.kill()
        await proc.wait()
        tmp.unlink(missing_ok=True)
        raise
    rc = await proc.wait()
    await err_task
    if rc != 0:
        tmp.unlink(missing_ok=True)
        raise RenderError(f"ffmpeg failed (exit {rc}):\n" + b"".join(err_chunks).decode(errors="replace"))
    os.replace(tmp, out)
    return info


def render_video(job: Job, audio: str | Path, out: str | Path, fps: int = 30, duration: float | None = None,
                 workers: int | None = None, crf: int = 20,
                 progress: Callable[[int, int], None] | None = None) -> SetupInfo:
    return _run(_video(job, str(audio), Path(out), fps, duration or job.total, workers or default_workers(),
                       crf, progress))


class Progress:
    """Prints frame progress, speed and time left to stderr."""

    def __init__(self, stream=sys.stderr):
        self.stream = stream
        self.tty = stream.isatty()
        self.start = time.monotonic()
        self.last = -1.0

    def __call__(self, done: int, total: int):
        now = time.monotonic()
        if done < total and now - self.last < (0.5 if self.tty else 10):
            return
        self.last = now
        elapsed = max(now - self.start, 1e-6)
        rate = done / elapsed
        left = (total - done) / rate if rate else 0
        msg = (f"  frame {done}/{total} ({100 * done // total}%)  {rate:.1f} frames/s  "
               f"elapsed {_mmss(elapsed)}  left {_mmss(left)}")
        if self.tty:
            self.stream.write("\r" + msg + ("\n" if done == total else ""))
        else:
            self.stream.write(msg + "\n")
        self.stream.flush()


def _mmss(seconds: float) -> str:
    seconds = int(round(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"
