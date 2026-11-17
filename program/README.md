# b2s-video

Turns a b2s song JSON and an MP3 into an MP4 lyric video. The lyrics are handwritten in a purple spiral notebook, and the page turns at the timestamps you give. The earlier storybook looks are still there with `--look kids` or `--look classic`. It works for any b2s song (any title, any number of sections, any tags) and renders 16:9 for YouTube and 9:16 for Shorts, Reels and TikTok.

Everything runs locally. Fonts are bundled, the page is blocked from the network, and nothing is uploaded.

## Setup (once)

You need Python 3.10 or newer, and ffmpeg with ffprobe on your PATH.

```
# ffmpeg (includes ffprobe)
winget install Gyan.FFmpeg          # Windows; open a new terminal afterwards
brew install ffmpeg                 # macOS
sudo apt install ffmpeg             # Debian/Ubuntu

# the tool
cd program
python -m venv .venv
.venv\Scripts\activate              # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
pip install -e .
python -m playwright install chromium
```

After this, `b2s-video --help` works whenever the venv is active.

## The workflow

1. **Make a timing file to fill in**

   ```
   b2s-video init-timing --song song.json --out turns.txt
   ```

   This writes one commented line per page, with a `00:00` placeholder under each:

   ```
   # page 2: Verse - "Two little kids in the big green wood,"
   00:00
   # page 3: Chorus - "Hand in hand, hand in hand,"
   00:00
   ```

2. **Fill in the times.** Listen to the song and replace each `00:00` with the moment that page starts. The turn into it runs from 0.25 s before that moment to 0.45 s after it. Page 1 (the cover) is shown from 0:00, so it has no line. Set each page about half a second before the first word of its section, and after the last word of the section before, so the turn falls in the gap between them. Or let `suggest-timing` (below) make a first draft.

3. **Check the times with a contact sheet** (takes seconds):

   ```
   b2s-video contact-sheet --song song.json --audio song.mp3 --turns-file turns.txt --out sheet.png
   ```

   This is a labeled grid with one still per page, taken 1 second after the page starts. Each cell shows the page number, the tag, the start time and the first line, so you can confirm that each page lines up with the music.

4. **Try a short piece, then render**

   ```
   b2s-video render --song song.json --audio song.mp3 --turns-file turns.txt --out preview.png --still 12
   b2s-video render --song song.json --audio song.mp3 --turns-file turns.txt --out test.mp4 --max-seconds 15
   b2s-video render --song song.json --audio song.mp3 --turns-file turns.txt --out song-16x9.mp4 --channel "My Channel"
   b2s-video render --song song.json --audio song.mp3 --turns-file turns.txt --out song-9x16.mp4 --format 9x16
   ```

   `render` is the default command, so `b2s-video --song ...` does the same thing.

## Preview in a browser (`preview`)

```
b2s-video preview --song song.json --audio song.mp3 --turns-file turns.txt --format 9x16 --out preview.html
```

This writes one HTML file that plays the song in its template with the audio: open it in any browser and press **Play** (or the space bar), and drag the bar to jump around. It uses the same template and timings as `render`, so it shows what the video will look like, without waiting for a render. It takes the same options (`--look`, `--format`, `--channel`, `--logo`, `--logo-mark`, `--no-subscribe`, `--line-timing`, `--highlight`, `--no-cover`, `--no-back-cover`).

- Fonts are embedded, and nothing is loaded from the internet.
- The audio is not copied into the file. The page finds it by its path relative to the HTML file, so keep the two in the same places (or make the preview again after moving them).
- `notebook.html` and `template.html` on their own show only the background: they are templates that b2s-video fills in. `preview` is the way to see one with a song.

## Shorts

There is no separate Shorts command: render the full 9:16 video, then cut a piece of it with ffmpeg. `-ss` is where the Short starts and `-t` how long it is, in seconds:

```
ffmpeg -y -ss 8.3 -i song-9x16.mp4 -t 36.2 -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart song-short.mp4
```

- A good piece is the cover opening, the first verse and the first chorus. Start at the cover's turn (0.25 s before page 2's timestamp).
- End after the chorus's last sung word and before the next page's turn starts (0.25 s before its timestamp), so the Short does not cut off a word or show a page turning at the end.
- This cut has no fades. Add `-vf "fade=..."` and `-af "afade=..."` if you want them.

## Upload text (`upload-text`)

```
b2s-video upload-text --song song.json
```

This writes the song JSON's `youtube` block (the video-upload-metadata skill adds it to a version) as plain text, with no JSON quotes, brackets or escapes, so each part can be pasted straight into YouTube Studio. It invents nothing: it only lays out what the JSON holds.

- The file goes to `out/<folder>-youtube.txt` inside the song's folder, beside the videos; `--out FILE` writes it somewhere else.
- It has a section for the regular video and one for the Short, each with the title (or title options), description, tags (comma-separated for the Tags box), thumbnail text, pinned comment and Studio settings, with character counts against YouTube's limits (title 100, description 5000, tags 500).
- Fields given once at the top of the `youtube` block are used by both parts. The skill's flat layout (`titles`, `shorts_title`, `shorts_description`), as in a standalone `<folder>.metadata.json`, works too.
- It prints any `{PLACEHOLDER}` still in the text (such as `{FULL_VIDEO_URL}`), to fill in after uploading.
- If you filled a placeholder in by hand in the text file (pasting the real link over `{FULL_VIDEO_URL}`), making the file again keeps what you pasted and says so. Put the link in the song JSON too, so it stays there for good.
- With several versions, it uses the one with a `youtube` block; `--version` picks one by number, channel or title.
- It replaces a file it wrote before, but not any other file at that path unless you pass `--force`.
- The JSON stays the source: change the text there, then run the command again.

## Timestamps

You need one timestamp for every page except the first, so **the count is the number of pages minus 1**. With a cover, 8 sections and a back cover there are 10 pages, so 9 timestamps. `--no-cover` and `--no-back-cover` change the count, so use the same flags for `init-timing`, `contact-sheet` and `render`.

Accepted formats (they can be mixed):

| Format | Example | Meaning |
|---|---|---|
| m:ss / mm:ss | `0:03`, `00:10`, `12:00` | minutes and seconds (seconds must have 2 digits) |
| with fractions | `1:05.5`, `01:05.25` | |
| h:mm:ss | `1:02:03`, `1:02:03.5` | |
| seconds | `74.5`, `3` | |

There are three equivalent ways to pass them:

1. Inline: `--turns "0:03,0:10,0:17"` (commas or spaces).
2. A text file: `--turns-file turns.txt`. One timestamp per line. `#` starts a comment, and blank lines are ignored.
3. A JSON file: `--turns-file turns.json` containing `{"turns": ["0:03", "0:10", 17.5]}`. A plain list `[3, 10, 17.5]` also works, so the prototype's `turns.example.json` still loads.

The timestamps are checked strictly before anything renders:

- **Wrong count.** The error says how many are expected and lists every page they map to, with its number, tag and first line, and shows which value landed where:
  ```
  9 timestamps expected, got 8.
    Page 2   Verse         "Two little kids in the big green wood,"   <- 0:03
    ...
    Page 10  Back cover                                               <- missing
  ```
- Timestamps must strictly increase, the first must be after 0:00, and every one must be before the audio ends.
- If you forget to fill in the `00:00` placeholders, the error tells you so.
- **Warnings (render continues):** a page on screen for less than 2 s, or a timestamp within 1 s of the end of the audio.

## Line timing inside a page

- `--line-timing all` (the default): all lines of a page appear together, fully visible, with no running highlight that follows the song.
- `--line-timing even`: lines light up one after another, spaced evenly from 0.4 s after the page starts to 0.8 s before the next page. Upcoming lines are dim and lines already reached stay dark. Even spacing is not synced to the singing.
- **Per-line times (optional).** In a JSON turns file, add a `lines` object keyed by page number, with one start time per line of that page. Those pages then use your times, and other pages follow `--line-timing`.
  ```json
  {"turns": ["0:03", "0:10", "..."],
   "lines": {"2": ["0:03.4", "0:05.1", "0:06.9", "0:08.2"]}}
  ```
  The times must increase, fall inside that page's time, and match its number of lines.
- `--highlight`: also marks the current line while it is "sung" (a yellow highlighter stroke in the notebook, berry red text in the storybook). It is off by default, because with even timing the red line can run ahead of or behind the singer. Turn it on when you use per-line times. It does nothing with `--line-timing all` unless the page has per-line times.

## Song JSON

The tool reads `lyrics` (required) plus `title`, `channel`, `source.work` and `source.author`, which are all optional.

- `lyrics` is an array of strings, one line per entry. A `[Tag]` entry starts a section and `""` ends it. Each section is one page.
- Any tag in brackets works. `Chorus` and `Hook` pages, including `Chorus 2` and `Final Chorus`, get the green double border in the storybook look. `Pre-chorus` does not. (In the notebook every page has the purple ♪ tab.) Tags outside the usual list (Intro, Verse, Pre-chorus, Chorus, Hook, Drop, Bridge, Solo, Build-up, Instrumental, Breakdown, Break, Interlude, Outro) produce a note, not an error.
- Tags are not shown on the pages. They decide the page breaks, the chorus border, and the labels in `init-timing` files and contact sheets.
- A section with no lines, such as `[Intro]` or `[Instrumental]`, becomes a page with just a small ornament.
- Missing fields:
  - no `title`: the file name is used ("my-song.json" becomes "My Song")
  - a bracketed note at the end of `source.work`, such as "(historical event, April 1912)", is left off the cover; it stays in the JSON
  - no `source.work`: no "after ..." line on the notebook cover (no "A song from the tale of ..." line on the storybook cover)
  - no `source.author`: no author line (the notebook cover never shows the author)
- **Several versions in one file.** If the JSON has a `versions` array (for example a kids and a general version), one version is used. It is the one whose title matches the audio file name (`A+Rose+in+the+Snow.mp3` picks "A Rose in the Snow"), or the one you name with `--version` (its number, channel or title, for example `--version general`). Top-level fields such as `source` are shared by all versions.
- Every song uses the notebook look unless you pass `--look kids` or `--look classic`. The `channel` field no longer picks the look.
- Straight apostrophes are shown as typographic ones (’). Lyric wording is never changed.

## Options

| Option | Default | |
|---|---|---|
| `--format 16x9\|9x16` | 16x9 | 1920x1080, or 1080x1920 with the text kept clear of the bottom 15% |
| `--look notebook\|kids\|classic` | notebook | purple spiral notebook in Caveat handwriting, or the storybook in Fredoka (rounded) or Lora (serif) |
| `--channel "Name"` | none | text on the back cover under "The end" |
| `--logo FILE` | none | your logo on the notebook cover, as a faint watermark behind the lyrics, and on The End page (see below) |
| `--logo-mark FILE` | none | a small symbol on the purple page tabs, in place of the ♪ |
| `--subscribe`, `--no-subscribe` | on | "Like & Subscribe" on The End page, under the logo, with "Subscribe" circled by hand (notebook look); `--no-subscribe` leaves it out |
| `--fps N` | 30 | |
| `--workers N` | half your CPU cores, at most 4 | Chromium processes rendering frames in parallel |
| `--crf N` | 20 | x264 quality; lower is better and bigger |
| `--line-timing all\|even` | all | all = whole page at once; even = lines light up one by one |
| `--highlight` | off | mark the current line (highlighter, or berry red in the storybook) |
| `--no-cover`, `--no-back-cover` | | |
| `--still SECONDS` | | save one PNG frame instead of a video |
| `--max-seconds N` | | render only the start, for tests |

The output is H.264 (yuv420p, BT.709), AAC 192 kb/s, with `+faststart`, and the same length as the audio. The file is written as `name.mp4.part` and renamed when ffmpeg finishes, so a failed render never leaves a broken MP4 behind.

## How it looks

Both templates are a pure function of time, `renderAt(t)`, with no CSS transitions, animations or timers, and Chromium runs with `--disable-partial-raster`, so every frame is exact and repeatable whatever was drawn before it.

### Notebook (default, `notebook.html`)

Based on `spiral-flipbook-purple.html`.

- **Pages, in order:** a purple cover with a label ("Singing Notebook", the title, "after {work}", a music note; no author) and at the bottom your `--logo` image, or else your `--channel` name (or "songs & stories"), one ruled page per section, and a last page with "The End", "thanks for listening", `--channel`, your `--logo` and "Like & Subscribe" with "Subscribe" circled (leave it out with `--no-subscribe`).
- **Page elements:** blue ruling, a red margin, punched holes, a spiral binding, a small music-note doodle and the page number. The lyrics sit on the ruled lines, a little above the middle of the page, in Caveat handwriting in ink `#6a2a62`. Section tags are not shown. Every page but the cover has the purple ♪ tab on the right edge (or your `--logo-mark`).
- **Page turn:** the page swings around the spiral, starting 0.25 s before each timestamp and lasting 0.7 s. Past halfway you see the ruled back of the page, and it fades out at the end of the swing.
- **Page shape:** 16:9 uses a landscape notebook page so lyric lines fit on one row at about 45 px. 9:16 uses the portrait notebook page, kept above the bottom 15%, with larger handwriting (about 52 px): long lines wrap onto the next ruled line, split evenly, instead of shrinking.
- **Fitting text:** like the storybook, every lyric page shares one text size. The ruling shrinks with the text so lines stay on it. Long lines wrap onto the next ruled line with a hanging indent, and the lyrics stay clear of the purple tab.

- **Logo (`--logo FILE`, `--logo-mark FILE`):** `--logo` puts your logo in three places:
  - the cover: centred at the bottom, about a fifth of the cover high, in its own colours, in place of the channel line;
  - every lyric page: a large, very faint watermark behind the lyrics;
  - The End page: the full logo under "thanks for listening".

  Inside the book the logo is drawn in the notebook's purple ink, whatever its own colour, using its transparent shape. `--logo-mark` puts a small symbol (for example just the quill) on the purple tab of every page, in white, in place of the ♪.

  Use PNGs (or WebP or SVG) with transparent backgrounds. A JPG cannot be transparent, so any background in it, even a painted checkerboard, shows on the cover, and inside the book the whole picture becomes a solid block; render warns about this. The images are built into the video and the preview, so they do not need to stay next to them.

  ```
  b2s-video render --song song.json --audio song.mp3 --turns-file turns.txt --format 9x16 --logo InkOfBallads_lineart.png --logo-mark InkOfBallads_quill.png --out song-9x16.mp4
  ```

### Storybook (`--look kids` / `--look classic`, `template.html`)

- **Pages, in order:** cover (title, "A song from the tale of {work}", author), one page per section, back cover ("The end" and `--channel`).
- **Page elements:** a parchment page with the lyric lines and a small page number at the bottom. Section tags are not shown.
- **Page turn:** a 3D swing around the left edge, starting 0.25 s before each timestamp and lasting 0.7 s, with easing and slight darkening.
- **Palette:** ink `#2B2A26`, forest `#2F5D46`, berry `#A63446`, background `#DCE3D8`.
- **Fitting text:** pages shrink their text so nothing is clipped. All lyric pages share one text size, chosen so that lines stay on one row where possible. Lines that are still too long wrap with a hanging indent. A page with far too much text, or an unbreakable word, shrinks further on its own. If a page still can't fit at 40% size, render prints a warning naming the page.
- **16:9 page shape:** the page is a wide storybook page. The prototype's tall 3:4 page forced typical lyric lines down to about 24 px at 1080p, which is too small to read. 9:16 keeps the tall 3:4 page.

## Speed

Frames are drawn by headless Chromium and captured straight over the DevTools protocol. Several browser processes render in parallel, and their frames are streamed to ffmpeg in order, with at most 3 × workers frames held in memory.

On the 12-core Windows laptop used to build this, at 1080p and 30 fps:

| Workers | Frames/s |
|---|---|
| 1 | 14 |
| 2 | 22 |
| 3 | 27 |
| 4 | 29 |

That is about real time. The notebook look renders at about the same speed (about 29 frames/s with 4 workers in 9:16), so a 2-minute song takes about 2 minutes. The prototype managed about 0.4 s per frame in its sandbox. Each worker uses roughly 150–250 MB of memory.

## Optional: suggested timestamps (`suggest-timing`)

```
pip install -r requirements-align.txt     # large: PyTorch, Whisper, Demucs
b2s-video suggest-timing --song song.json --audio song.mp3 --out turns.txt [--separate-vocals]
```

- **How it works:** it runs stable-ts forced alignment locally. The first run downloads the Whisper `base` model (about 140 MB).
- **Output:** the same file format as `init-timing`, filled in, with a confidence note at the top and in the terminal.
- **`--separate-vocals`:** runs Demucs first, which can help with loud backing tracks.
- **Your timestamps win:** it never overwrites an existing file without `--force`, and render uses exactly what the file says. Treat the result as a first draft, and check it with `contact-sheet`.
- **Check it by ear.** A low-confidence first word can put a turn seconds too early, while the previous section's last line is still being sung. That happened on several pages of both songs made so far. Listen around each turn, or compare with a word-by-word transcription, and move any turn that cuts into a line.

It was tested on Python 3.10 in a separate venv (`.venv-align`), so the main install stays small.

## Troubleshooting

- **`ffmpeg was not found on PATH`** (or ffprobe). Install ffmpeg (see Setup) and open a new terminal. On Windows, winget adds it to PATH only for new terminals.
- **`Chromium for Playwright is not installed`.** Run `python -m playwright install chromium` with the venv active.
- **`9 timestamps expected, got 8`.** Read the page list in the message and find the missing or extra line. Also check that `--no-cover` and `--no-back-cover` match the ones used for `init-timing`.
- **`Every timestamp is 0:00`.** You haven't filled in the placeholders from `init-timing` yet.
- **`seconds must be 00-59` / `write seconds with two digits`.** Write `1:05`, not `1:65` or `1:5`.
- **A page turns too early or late.** Look at the contact sheet, then move that page's timestamp. The turn runs from 0.25 s before the timestamp to 0.45 s after it, so it should fall between the last word of one section and the first word of the next.
- **Text looks small.** A single very long line sets the size for the whole book. Shorter lines, or one more section, keep the text large.
- **Warning that a page has too much text.** Split the section into two.
- **Very slow render.** Lower `--fps` (24 is fine for lyrics) or raise `--workers` if you have spare cores and memory.

## Tests

```
pip install -r requirements-dev.txt
python -m pytest
```

- **Unit tests:** lyrics parsing (empty sections, missing source, unknown tags), every timestamp format and bad input, the page-count check and its message, line timing, and the upload text (both youtube layouts, version choice, placeholders, not replacing other files).
- **Different songs:** three songs in `tests/data` (with Intro and Instrumental pages, an 8-line verse, a very long line, an unbreakable word, no source, an unknown tag) prove nothing is tied to one song.
- **Browser tests:** for the notebook and storybook looks, they check that every page fits in both formats and that frames are deterministic. They also check that tags are never shown, the logo appears on the cover, every lyric page, The End page and the tabs, and the browser preview loads with its audio.
- **ffmpeg smoke test:** it renders 5 s at 6 fps and checks with ffprobe for H.264, AAC and the right duration.
- **Skipping:** browser and ffmpeg tests skip themselves when Chromium or ffmpeg is missing.

## Files

```
b2s_video/          the package (cli, song, timing, render, contact, preview, suggest, upload, notebook.html, template.html)
b2s_video/assets/fonts/   Caveat, Fredoka and Lora (SIL Open Font License, licences included)
tests/              pytest suite and test songs
reference/          the original prototype, kept for comparison
requirements*.txt   pinned dependencies (runtime, dev, optional alignment)
```
