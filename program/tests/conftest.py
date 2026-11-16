import shutil
import subprocess
from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


def _chromium_ok() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
HAVE_CHROMIUM = _chromium_ok()

needs_browser = pytest.mark.skipif(not HAVE_CHROMIUM, reason="Chromium for Playwright is not installed")
needs_ffmpeg = pytest.mark.skipif(not HAVE_FFMPEG, reason="ffmpeg/ffprobe not on PATH")


@pytest.fixture(scope="session")
def tone(tmp_path_factory):
    """A 5 second MP3 test tone."""
    if not HAVE_FFMPEG:
        pytest.skip("ffmpeg/ffprobe not on PATH")
    path = tmp_path_factory.mktemp("audio") / "tone.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
                    "-c:a", "libmp3lame", "-b:a", "128k", str(path)], check=True)
    return path
