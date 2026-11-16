"""A single HTML file that plays a song in its page template, in the browser, with the audio.

It is the same template and the same renderAt(t) the video uses, so what you see is what renders.
Fonts are embedded; the audio is linked by a path relative to the HTML file.
"""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

from .render import TEMPLATES, Job

FONT_TYPES = {".woff2": "font/woff2", ".ttf": "font/ttf"}

PLAYER = """
<style id="b2s-preview">
html{background:#111}
body{transform-origin:0 0}
#b2s-bar{position:fixed;left:0;right:0;bottom:0;display:flex;gap:12px;align-items:center;padding:10px 16px;
  background:rgba(0,0,0,.72);color:#eee;font:14px/1.2 "Segoe UI",Arial,sans-serif;z-index:99999}
#b2s-bar button{font:inherit;color:inherit;background:#333;border:1px solid #666;border-radius:6px;padding:5px 14px;cursor:pointer}
#b2s-bar input{flex:1}
#b2s-bar span{min-width:96px;text-align:right;font-variant-numeric:tabular-nums}
</style>
<script>
(async () => {
  const CFG = __CFG__, AUDIO = __AUDIO__, TOTAL = __TOTAL__;
  await window.setup(CFG);
  const bar = document.createElement("div");
  bar.id = "b2s-bar";
  bar.innerHTML = '<button id="b2s-play">Play</button><input id="b2s-seek" type="range" min="0" step="0.01"><span id="b2s-time"></span>';
  document.documentElement.append(bar);    // outside body, so the scaling below does not shrink it
  const audio = new Audio(AUDIO), play = bar.querySelector("#b2s-play"),
        seek = bar.querySelector("#b2s-seek"), time = bar.querySelector("#b2s-time");
  seek.max = TOTAL;
  const mmss = s => Math.floor(s / 60) + ":" + String(Math.floor(s % 60)).padStart(2, "0");
  let t = 0;
  const fit = () => {
    const s = Math.min(innerWidth / CFG.W, (innerHeight - bar.offsetHeight) / CFG.H);
    document.body.style.transform = "scale(" + s + ")";
    document.body.style.marginLeft = (innerWidth - CFG.W * s) / 2 + "px";
  };
  addEventListener("resize", fit);
  fit();
  const draw = () => {
    if (!audio.paused) t = audio.currentTime;
    window.renderAt(t);
    seek.value = t;
    time.textContent = mmss(t) + " / " + mmss(TOTAL);
    requestAnimationFrame(draw);
  };
  play.onclick = () => audio.paused ? audio.play().catch(e => alert("The audio could not play: " + e.message)) : audio.pause();
  audio.onplay = () => { play.textContent = "Pause"; };
  audio.onpause = () => { play.textContent = "Play"; };
  seek.oninput = () => { t = +seek.value; audio.currentTime = t; };
  addEventListener("keydown", e => { if (e.key === " ") { e.preventDefault(); play.click(); } });
  draw();
})();
</script>
"""


def _embed_fonts(html: str, base: Path) -> str:
    def data_uri(m: re.Match) -> str:
        path = base / m.group(1)
        kind = FONT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        return f'url("data:{kind};base64,{base64.b64encode(path.read_bytes()).decode()}")'
    return re.sub(r'url\("(assets/fonts/[^"]+)"\)', data_uri, html)


def _audio_src(audio: Path, out: Path) -> str:
    audio, folder = audio.resolve(), out.resolve().parent
    try:
        return quote(Path(os.path.relpath(audio, folder)).as_posix())
    except ValueError:                       # another drive on Windows
        return audio.as_uri()


def write_preview(job: Job, audio: str | Path, out: str | Path) -> Path:
    out = Path(out)
    template = TEMPLATES[job.look]
    html = _embed_fonts(template.read_text(encoding="utf-8"), template.parent)
    player = (PLAYER.replace("__CFG__", json.dumps(job.config(), ensure_ascii=False))
                    .replace("__AUDIO__", json.dumps(_audio_src(Path(audio), out)))
                    .replace("__TOTAL__", json.dumps(round(job.total, 3))))
    out.write_text(html.replace("</body>", player + "</body>", 1), encoding="utf-8")
    return out
