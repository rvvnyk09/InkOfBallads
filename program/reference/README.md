# b2s page-turn video renderer

Turns a b2s song JSON plus an MP3 into an MP4 where the lyrics sit on a book page and the page turns for each section.

## Setup (once)
- Python 3.9+, ffmpeg (with ffprobe) on your PATH
- `pip install playwright` then `playwright install chromium`

## Render
```
python render.py --song hand-in-hand.json --audio Hand_in_Hand.mp3 \
    --turns turns.json --format 16x9 --out hand-in-hand.mp4
```
Options: `--format 16x9` (YouTube, 1920x1080) or `9x16` (Shorts, Reels, TikTok, 1080x1920), `--fps 30`, `--look kids|classic`, `--channel "Your channel"` (shown on the back cover), `--crf 20` (lower is better quality).

## Preview before a full render
- One frame: `--still 12 --out preview.png` saves the page as it looks at 12 seconds.
- Short test: `--max-seconds 15 --fps 15 --out test.mp4`.

## Turn times (the important part)
`turns.json` is a list of start times in seconds, one for each lyric section after the cover, plus one for the back cover. The cover is shown from 0:00 until the first time. For the sample song (8 sections) that is 9 numbers:
```
{"turns": [3.0, 10.0, 17.0, 24.0, 31.0, 38.0, 45.0, 52.0, 58.0]}
```
- Page 1 (cover) starts at 0. The first number is when the first Verse page starts.
- The page-turn animation starts 0.25 s before each time and lasts 0.7 s.
- If `--turns` is left out, the script spreads the sections evenly across the song as a placeholder. That runs, but it will not match the music.
- Get real times by listening to the song and noting where each section starts.

## How the lyrics are shown
Lines fade in one by one within each page, evenly spaced between that page's start time and the next. They are not synced to individual sung words.

## Notes
- Rendering is frame by frame, so it is slow. In the test sandbox it took about 0.4 s per frame at 1080p, so a 2-minute song at 30 fps took roughly 25 minutes. Try `--fps 24`, and a faster machine will do better.
- Fonts come from Google Fonts. Without internet access the page falls back to system fonts, which look plainer.
- The song JSON is the b2s format. Section tags become page labels, and a `[Chorus]` page gets a green border.
- Upload the finished MP4 to YouTube yourself. Mark Kids channel videos as made for kids.
