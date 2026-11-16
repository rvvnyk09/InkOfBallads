# InkOfBallads – b2s-video

Makes the InkOfBallads "Singing Notebook" lyric videos from a b2s song folder (song JSON + MP3).

| Folder | What it is |
|---|---|
| `program/` | The `b2s-video` Python program (render, preview, contact sheet, suggest-timing). See `program/README.md` for setup and every option. |
| `skill/b2s/` | Lyrics skill: writes the b2s song JSON (lyrics, style prompt, safety check) for public-domain stories. |
| `skill/b2s-video/` | Video skill that drives the program (`SKILL.md` + `scripts/check_timings.py`). |
| `skill/video-upload-metadata/` | Titles, descriptions, tags and hashtags for YouTube, Shorts, TikTok and Reels uploads. |
| `logos/` | Cover logo (`InkOfBallads_lineart.png`) and tab mark (`InkOfBallads_quill.png`) passed as `--logo` / `--logo-mark`. |
| `design/` | Early notebook/flipbook HTML prototypes and the lyric-writing note (`Notes.txt`). |

Workflow: **b2s** (write lyrics) → generate the music elsewhere → **b2s-video** (make the videos) → **video-upload-metadata** (upload text).

## Setup on a new machine

1. Install Python 3.10+ and ffmpeg/ffprobe (on PATH).
2. Create the two virtual environments inside `program/`, as described in `program/README.md`:
   - `.venv` – `pip install -r requirements.txt`, `pip install -e .`, then `python -m playwright install chromium` (render, preview, contact sheet)
   - `.venv-align` (Python 3.10) – also `pip install -r requirements-align.txt` (Whisper alignment, suggest-timing, timing checker)
3. Copy each folder in `skill/` to `%USERPROFILE%\.claude\skills\` so Claude Code can use the skills (or zip a folder as `<name>.skill` to upload it to claude.ai).
4. Update the paths in the b2s-video skill's "Where things are" table if the folders live somewhere else.

Song folders (MP3s, JSON, rendered videos) are not stored in this repo.
