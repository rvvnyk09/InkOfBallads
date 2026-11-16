"""A labeled grid of stills, one per page, to check timestamps before a long render."""
from __future__ import annotations

import asyncio
import base64
import html
from pathlib import Path

from .render import Job, _launch, _stills
from .timing import TURN_LEAD, format_timestamp

STILL_OFFSET = 1.0   # seconds after a page starts


def still_times(starts: list[float], total: float) -> list[float]:
    """One second after each page starts, or earlier if the next turn begins before that."""
    out = []
    for i, s in enumerate(starts):
        end = starts[i + 1] - TURN_LEAD if i + 1 < len(starts) else total
        t = s + STILL_OFFSET
        if t >= end:
            t = s + max(end - s, 0) / 2
        out.append(min(t, max(total - 0.01, 0)))
    return out


def _sheet_html(job: Job, shots: list[bytes], times: list[float]) -> tuple[str, int]:
    w, h = job.size
    cols, thumb_w = (4, 460) if w > h else (6, 300)
    thumb_h = round(thumb_w * h / w)
    cells = []
    for p, shot, start, t in zip(job.pages, shots, job.starts, times):
        first = html.escape(p.first_line) if p.first_line else ("<i>no lines</i>" if p.kind == "section" else "&nbsp;")
        img = base64.b64encode(shot).decode()
        cells.append(
            f"<figure><img src='data:image/jpeg;base64,{img}' width='{thumb_w}' height='{thumb_h}'>"
            f"<figcaption><b>Page {p.number}</b> &middot; {html.escape(p.label)}"
            f"<span>starts {format_timestamp(start)} &middot; still at {format_timestamp(t)}</span>"
            f"<em>{first}</em></figcaption></figure>")
    title = html.escape(job.title)
    width = cols * thumb_w + (cols - 1) * 18 + 2 * 28
    doc = f"""<!doctype html><meta charset="utf-8"><style>
body{{margin:0;background:#F4F1E8;font:14px/1.35 "Segoe UI",Arial,sans-serif;color:#2B2A26;width:{width}px}}
header{{padding:22px 28px 6px;font-size:20px}} header small{{color:#6B6554;font-size:14px;margin-left:10px}}
main{{display:grid;grid-template-columns:repeat({cols},{thumb_w}px);gap:18px;padding:14px 28px 28px}}
figure{{margin:0;background:#fff;border:1px solid #D6D0BF;border-radius:6px;overflow:hidden}}
img{{display:block;width:{thumb_w}px;height:{thumb_h}px}}
figcaption{{padding:8px 10px 10px}} figcaption span{{display:block;color:#2F5D46}}
figcaption em{{display:block;color:#6B6554;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
</style><header>{title}<small>{len(job.pages)} pages &middot; {job.format} &middot; audio {format_timestamp(job.total)}</small></header>
<main>{''.join(cells)}</main>"""
    return doc, width


async def _sheet(job: Job, out: Path):
    from playwright.async_api import async_playwright
    times = still_times(job.starts, job.total)
    shots, info = await _stills(job, times, "jpeg")
    doc, width = _sheet_html(job, shots, times)
    async with async_playwright() as pw:
        browser = await _launch(pw)
        try:
            page = await browser.new_page(viewport={"width": width, "height": 400}, device_scale_factor=1)
            await page.set_content(doc)
            await page.screenshot(path=str(out), full_page=True, type="png")
        finally:
            await browser.close()
    return times, info


def contact_sheet(job: Job, out: str | Path):
    return asyncio.run(_sheet(job, Path(out)))
