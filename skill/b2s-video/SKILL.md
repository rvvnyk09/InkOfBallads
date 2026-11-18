---
name: b2s-video
description: Make the InkOfBallads "Singing Notebook" lyric videos from a b2s song folder (a b2s song JSON plus its MP3) with the local b2s-video program - checked page-turn timings, the full 9:16 video with the InkOfBallads logos and a 16:9 version that shows the 9:16 notebook zoomed to fill the height for regular YouTube, a Short cut from the 9:16, thumbnails from the cover (9:16 opening slide and 16:9), a browser preview, and the YouTube upload text (`<folder>-youtube.txt`, ready to paste), writing the song JSON's `youtube` block first when it is missing. Use this skill whenever the user asks to create, make, render or redo a video, lyric video, Short, Reel, TikTok, thumbnail or preview for a song or song folder (for example "create video for ...\CreateVideo\some-song"), wants page timings checked or fixed, wants the upload text or YouTube details for a song folder, or asks how to run b2s-video, even if they do not name the program. Not for writing lyrics (that is the b2s skill), or for upload metadata for videos that are not b2s song folders (video-upload-metadata).
---

# b2s-video: Singing Notebook lyric videos

The user writes songs with the b2s skill, generates the music elsewhere, and keeps each song in its own folder under `CreateVideo`. This skill turns such a folder into finished videos with the user's b2s-video program. Accuracy of the page turns is what makes or breaks these videos: a page that turns while a line is still being sung looks broken, and the program's automatic timings got several pages wrong on every song so far. So most of the care goes into step 2.

## Where things are

| What | Path |
|---|---|
| Song folders | `C:\RV\Laptop Backup - 07.09.2022\Work\Book\CreateVideo\<song-folder>` |
| Program (and its README) | `C:\RV\Laptop Backup - 07.09.2022\Work\Book\CreateVideo\program` |
| Main venv (render, preview, contact sheet) | `program\.venv\Scripts\b2s-video.exe` |
| Alignment venv (Whisper, suggest-timing, this skill's checker) | `program\.venv-align\Scripts\` (`b2s-video.exe`, `python.exe`) |
| Cover logo (gold line art, transparent) | `C:\RV\Laptop Backup - 07.09.2022\Work\Book\InkOfBallads_lineart.png` |
| Tab mark (quill only, transparent) | `C:\RV\Laptop Backup - 07.09.2022\Work\Book\InkOfBallads_quill.png` |
| Timing checker | `scripts/check_timings.py` in this skill |
| Short's "Watch the full song" pill (transparent 1080x1920 PNG) | `program\b2s_video\assets\full-song-pill.png`, drawn by `scripts/make_full_song_pill.py` in this skill |

If a path does not exist, look for it nearby before asking; the user may have moved the folder. Use the Bash tool with forward slashes and quote every path, since they contain spaces. The program's README has the full option list; read it when the user asks for something this file does not cover.

## Defaults (what the user has chosen)

- **Both formats**: 9:16 (1080x1920) for Shorts, Reels and TikTok, and 16:9 (1920x1080) for regular YouTube. YouTube files every square or vertical upload of 3 minutes or less as a Short, with no way to opt out, so the 16:9 file is what the user uploads as the regular video. The 16:9 file is the **portrait-zoomed 9:16** ("option A"): the 9:16 video's notebook, cropped tight and scaled up to fill the height of a 1920x1080 frame on the same green background, with the gold logo on the right (step 4). The user chose it on 2026-11-17 from tryouts in `pay-the-piper\16x9-tryouts` because the lyrics are 1.5x bigger than in the earlier framed 9:16 (about 46 px tall instead of 31), which matters on a phone held upright; the landscape-notebook tryouts B and C had bigger text but were not chosen. Its lyrics are also one size bigger than the 9:16's (`--font-size 32` instead of 31, so about 47 px tall): the 16:9 is built from its own 9:16 render at that size (step 4). The program's own `--format 16x9` template draws a landscape notebook that fills the screen with small lyrics; the user found it too big, so do not use it for the video unless asked.
- **If the user asks whether a 9:16 video can be a regular YouTube video**: only if it is longer than 3 minutes (for example by holding The End page longer), and YouTube then shows it with side bars on desktop and TV. For songs under 3 minutes the portrait-zoomed 16:9 is the answer.
- **Background colour**: forest green, the template's `--desk` colour in `program/b2s_video/notebook.html`. The program has no option for it yet. The user has seen mock-ups of midnight navy, walnut wood, charcoal slate, deep teal and burgundy (burgundy blends with the purple cover). Changing the colour is a template change (see "Things to avoid"); after it, the bottom strip the 16:9 background is taken from changes colour with it, so the 16:9 needs no other change. Mock-ups need no program change: recolour the green pixels of a 9:16 frame (green where G > R+4, G > B+4 and R < 120), scaling the new colour by each pixel's brightness so the texture and shadow stay.
- **Thumbnails**: two. The user's preferred one is the 9:16 video's opening slide (the notebook cover at 1 s), saved as it is, 1080x1920 JPG, for Shorts, Reels and TikTok covers. There is also the 16:9 cover, 1280x720 JPG, for the regular YouTube upload (YouTube shows regular-video thumbnails as 16:9, so a 9:16 image would get side bars there). Never change the 9:16 or 16:9 videos to add a thumbnail (no title slide spliced in): the user said so. The user has seen designed title thumbnails (big title on a purple cover, a notebook page, a chorus line) and chose the plain opening slide; do not make designed ones unless asked.
- **Notebook look**, the program's default. No `--line-timing` flag: the default `all` shows each page's lines at once, which the user wants; the running line-by-line effect (`even`) and `--highlight` stay off unless asked.
- **Logos on**: `--logo` (cover, faint page watermark, The End page) and `--logo-mark` (quill on the page tabs).
- **Like & Subscribe on**: the program writes, by default (no flag needed; `--no-subscribe` turns it off), "Like & Subscribe" in the notebook handwriting on The End page, under the logo, with "Subscribe" circled by hand. The user chose this (option 11 of 16 mock-ups in `CreateVideo\mockups\like-subscribe-on-page-*.png`) over a pill below the notebook: it stays on the page, so the 16:9 recipe in step 4 needs no change. It is in the 9:16 and 16:9 videos but not in the Short, which ends before The End page.
- **No `--channel`**: the user removed "Book to Song" text. With a logo, the cover shows the logo instead.
- **Short**: verse 1 and the first chorus, cut from the full video, no fades at either end, under 60 s, with the **"▶ Watch the full song" pill** fading in below the notebook for the last 3 s (step 5). The user chose this (option 1 of 5 in `CreateVideo\mockups\full-ballad-cue-*.png`) because it reads the same on phones and desktop: an earlier "Full ballad · tap below" pill with a down arrow only made sense on a phone, since YouTube puts the Related video link somewhere else on desktop. So never write "tap", "below" or arrows into it; the gold ▶ is what ties it to the ▶ on YouTube's Related video link.
- Outputs go in `<song-folder>\out\`, named after the folder: `<folder>-9x16.mp4`, `<folder>-16x9.mp4`, `<folder>-short-<N>s.mp4` (N = rounded length), `<folder>-thumbnail.jpg` (16:9), `<folder>-thumbnail-9x16.jpg`, `<folder>-preview.html`, `sheet-9x16.png`, and `<folder>-youtube.txt` (the upload text, step 8; the skill writes the song JSON's `youtube` block first if it is missing).

## Workflow

### 1. Look at the folder

List it and read the song JSON. Note the title, the sections (each `[Tag]` section becomes one notebook page; the page count is sections + 2 for cover and back cover) and the MP3's name and length (`ffprobe -v error -show_entries format=duration -of csv=p=0 "<mp3>"`). If the JSON has a `versions` array, the program picks the version whose title matches the MP3 name; otherwise pass `--version`. If there is a `turns.txt`, read it: real times in it are the user's work.

### 2. Get page-turn timings and check them

Each timestamp is when a page starts; the page swings from 0.25 s before it to 0.45 s after. A good time puts the whole swing in the pause between the last word of one section and the first word of the next.

1. If there is no usable `turns.txt` (missing, or only `00:00` placeholders), make a first draft:
   ```
   "<program>/.venv-align/Scripts/b2s-video.exe" suggest-timing --song "<json>" --audio "<mp3>" --out "<folder>/out/turns.suggested.txt"
   ```
2. Check the draft (or the user's own file) against what is actually sung:
   ```
   "<program>/.venv-align/Scripts/python.exe" "<skill>/scripts/check_timings.py" --song "<json>" --audio "<mp3>" --turns "<turns file>" --write "<folder>/turns.txt"
   ```
   It transcribes the song with Whisper (cached next to the MP3 as `<mp3>.words.json`), then for every turn prints `ok`, `tight` (the pause is shorter than the swing; the time is already the best possible) or `CLASH` with the words sung during the swing and a suggested time. `--write` saves the suggested times as a commented timing file; it refuses to overwrite without `--force`, and you should only pass `--force` over a file you made or one that holds only placeholders. Never overwrite timings the user typed in themselves without asking.
3. Read the report rather than trusting it blindly. Whisper mishears sung words ("Merry men" comes out as "Mary men"), sometimes misses whole lines, and can match the wrong line. Lines marked "check by ear" or a suggestion that moves a page more than about 2 s deserve a second look at the transcription (`<mp3>.words.json`) around that time. Adjust the written file by hand where needed, and keep a short comment per page saying what is sung there, so the user can follow your reasoning.
4. Run the checker once more on the final file. Every page should be `ok` or `tight`.

### 3. Contact sheet

```
"<program>/.venv/Scripts/b2s-video.exe" contact-sheet --song "<json>" --audio "<mp3>" --turns-file "<folder>/turns.txt" --format 9x16 --logo "<lineart>" --logo-mark "<quill>" --out "<folder>/out/sheet-9x16.png"
```

Look at the image (Read it). Check that each page shows its own section, no text is clipped or runs under the purple tab, the cover title fits, and The End page shows the logo and "Like & Subscribe" with "Subscribe" circled. The render prints a warning if a page has too much text; a section that long is better split by the user than shrunk.

### 4. Render the full videos

Render the 9:16 video:

```
"<program>/.venv/Scripts/b2s-video.exe" render --song "<json>" --audio "<mp3>" --turns-file "<folder>/turns.txt" --format 9x16 --logo "<lineart>" --logo-mark "<quill>" --out "<folder>/out/<folder>-9x16.mp4"
```

It renders at roughly real time (a 2.5-minute song takes about 2.5 minutes), so give it a 10-minute timeout, or run it in the background and do other steps meanwhile. If the laptop may sleep during a long run, ask the app to keep it awake (`request_keep_awake`); one render that the machine slept through took 3 hours. If an output file already exists and you are replacing it, write to a `.new.mp4` name and move it over the old one only after it succeeds.

The 16:9 is built from a **second 9:16 render with the lyrics one size bigger** (`--font-size 32` instead of the default 31), which the user asked for on 2026-11-17: the 16:9 lyrics should be a little bigger than the 9:16's. This render is only a source for the 16:9, not a deliverable, so write it to the scratchpad. It takes as long as the first one; run both at once in the background (`--workers 2` each) to save time:

```
"<program>/.venv/Scripts/b2s-video.exe" render --song "<json>" --audio "<mp3>" --turns-file "<folder>/turns.txt" --format 9x16 --logo "<lineart>" --logo-mark "<quill>" --font-size 32 --out "<scratchpad>/<folder>-9x16-for-16x9.mp4"
```

Before rendering, make a contact sheet with the same `--font-size 32` (to the scratchpad) and check that every page still fits; the bigger size can wrap a long line onto one more ruled line (Pay the Piper's verse 2 did), which is fine as long as nothing is clipped.

Then build the 16:9 video from that source with ffmpeg (about a minute per song):

```
ffmpeg -v error -y -i "<scratchpad>/<folder>-9x16-for-16x9.mp4" -loop 1 -i "<lineart>" -filter_complex "[0:v]split[a][b];[a]crop=1080:300:0:1610,scale=1920:1080,setsar=1[bg];[b]crop=1080:1300:0:140,scale=898:1080:flags=lanczos,setsar=1[fg];[1:v]scale=300:-1[logo];[bg][fg]overlay=470:0[t];[t][logo]overlay=1520:(H-h)/2,format=yuv420p[v]" -map "[v]" -map 0:a -shortest -c:v libx264 -preset medium -crf 20 -r 30 -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a copy -movflags +faststart "<folder>/out/<folder>-16x9.mp4"
```

How it works: the background is the 9:16 video's bottom strip (rows 1610 to 1910, always plain green) stretched to fill the frame; the notebook is rows 140 to 1440 of the 9:16 video (the book sits at about rows 183 to 1420), scaled 1.5x to 898x1080 and placed at x=470, a little left of centre to leave room for the logo, which is 300 px wide at x=1520, vertically centred. The crop is tight on purpose: during a page turn the top and bottom of the swinging page touch the frame edge for a split second, which the user accepted. If the template's layout changes, measure again before trusting these numbers. (The earlier recipe, which the user replaced, framed the whole 9:16 at 720x1080: `crop=1080:1620:0:0,scale=720:1080`, overlay at x=600, logo 320 px at x=1540.)

Confirm both results with ffprobe: h264 at 1080x1920 and 1920x1080, aac, the MP3's duration. The 16:9 file is built from its own size-32 9:16 render, so render that again and rebuild the 16:9 whenever the 9:16 is re-rendered (new timings, lyrics or template). The Short is still cut from the normal 9:16 (`<folder>-9x16.mp4`), not from the size-32 source.

### 5. Cut the Short (from the 9:16 video)

`check_timings.py` ends its report with a suggested Short (start, length, the last word inside it, and the ffmpeg command). The Short starts as the cover opens and ends after the first chorus's last word, before the next page begins to turn, so it neither cuts a word off nor ends mid-turn.

Cut it with this command, not the shorter one the report prints: it also lays the "Watch the full song" pill over the last 3 s. `<pill>` is `program/b2s_video/assets/full-song-pill.png`, and `<length-3>` is the length minus 3, worked out by you (for a 45.7 s Short, 42.7):

```
ffmpeg -v error -y -ss <start> -i "<folder>/out/<folder>-9x16.mp4" -loop 1 -framerate 30 -i "<pill>" -t <length> -filter_complex "[1:v]format=rgba,fade=t=in:st=<length-3>:d=0.4:alpha=1[p];[0:v][p]overlay=0:0:enable='gte(t,<length-3>)':shortest=1,format=yuv420p[v]" -map "[v]" -map 0:a -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -b:a 192k -movflags +faststart "<folder>/out/<folder>-short-<N>s.mp4"
```

The pill fades in over 0.4 s and then stays; it does not move. It sits at rows 1470 to 1580, centred, in the green space under the notebook (the book ends at about row 1420), clear of YouTube's buttons on the right and its title, channel and Related video link at the bottom. If the pill's wording or look ever changes, change `scripts/make_full_song_pill.py` and run it again with the main venv's `python.exe` (`--fonts "<program>/b2s_video/assets/fonts" --out "<pill>"`); do not edit the PNG by hand.

No fades on the video itself: the user does not want them (the pill's own fade-in is the one exception). When replacing an earlier Short, delete it first so the new file's created date is fresh (Windows keeps the old one otherwise, which confused the user once). Then verify the ending: transcribe the last 5 s of the Short with Whisper and make sure the chorus's last words are there.

### 6. Thumbnails

The 9:16 thumbnail is the opening slide of the finished 9:16 video, 1 s in:

```
ffmpeg -v error -y -ss 1 -i "<folder>/out/<folder>-9x16.mp4" -frames:v 1 -q:v 2 "<folder>/out/<folder>-thumbnail-9x16.jpg"
```

For the 16:9 thumbnail, save the cover as a still from the 16:9 template, 1 s in (the cover is fully shown), and scale it to YouTube's recommended 1280x720 JPG (the limit is 2 MB; this comes out near 120 KB):

```
"<program>/.venv/Scripts/b2s-video.exe" render --song "<json>" --audio "<mp3>" --turns-file "<folder>/turns.txt" --format 16x9 --logo "<lineart>" --logo-mark "<quill>" --still 1 --out "<scratchpad>/cover-16x9.png"
```
```
ffmpeg -v error -y -i "<scratchpad>/cover-16x9.png" -vf "scale=1280:720:flags=lanczos" -q:v 2 "<folder>/out/<folder>-thumbnail.jpg"
```

Read both JPGs and check that the title, "after ..." line and logo are sharp and nothing is cut off. If the user wants different thumbnail text (a bigger title, a hook line), that is a template change: offer a mock-up first, as under "Things to avoid".

### 7. Browser preview

```
"<program>/.venv/Scripts/b2s-video.exe" preview --song "<json>" --audio "<mp3>" --turns-file "<folder>/turns.txt" --format 9x16 --logo "<lineart>" --logo-mark "<quill>" --out "<folder>/out/<folder>-preview.html"
```

Make it in 9:16 (the user's preview format). One HTML file that plays the song in the template with the audio (Play button, space bar, seek bar). It finds the MP3 by relative path, so it must stay in `out\` beside the song folder.

### 8. YouTube details and upload text (plain text to copy and paste)

Every video run ends with an upload text file. It comes from the `youtube` block in the song JSON's version, so first make sure that block exists.

**8a. If the version has no `youtube` block, write one.** Follow the video-upload-metadata skill's rules (read its `SKILL.md` and `references/platforms.md`: hard limits, the made-for-kids and AI-disclosure checks, no misleading tags), but write it in the house layout below, not that skill's own JSON shape, and add it only to the version the video was made from. Where the house rules below differ from that skill (title pattern, no chapters, the Short sharing the description), the house rules win: the user set them on 2026-11-17. Copy the layout, links and tone from `pay-the-piper`, the first song done fully in this layout (look for others with `grep -l '"youtube"' */*.json`; older ones such as `your-eyes-feel-like-home` still have chapters and their own Short description).

- `links`: `handle_url` `https://www.youtube.com/@InkOfBallads`, `subscribe_url` `https://www.youtube.com/channel/UChThLWqUGxCJsx-TYefVNlw?sub_confirmation=1`, and `{FULL_VIDEO_URL}`, `{SHORT_URL}` (as `short_url`), `{PLAYLIST_URL}`, `{NEXT_VIDEO_URL}`, `{SOURCE_TEXT_URL}` as placeholders.
- `normal` (the 16:9 upload) and `short` (the Short), each with `title`, `description`, `tags`, `hashtags`, `pinned_comment` and `studio_settings` (`made_for_kids`, `ai_use_disclosure`, `category` Music, `language`, and `playlist` for `normal`); `normal` also gets `thumbnail_text`.
- **Regular video title**: `Full Song | <song title> | <what it is>`, ending in **Ballad** when the song is from a book, story, legend, play or historical event (the JSON has a `source`), and in **Song** when it is a personal lyric with no source. For example `Full Song | Pay the Piper | Pied Piper of Hamelin Ballad` (the user's own title), or for a personal lyric something like `Full Song | Your Eyes Feel Like Home | Sweet Love Song`. The middle part is the song's title exactly; the last part names the source work (for a ballad) or the kind of song (for a personal lyric) in a few words. Never add "(Lyric Video)", "Lyrics" or other labels to the title. Keep it short (under about 60 characters if possible): starting with "Full Song" pushes the searchable words later, and phones cut long titles. The Short's title stays as before (song title first, then a short hook, under 100 characters).
- **Description** (a list of lines), in this order: the hook line; a blank line; a short summary; a blank line; the source credit from the JSON's `source` with "Original song ... AI-assisted music and lyrics" (for a personal lyric just "Original song. AI-assisted music and lyrics."); a blank line; a comment prompt; a blank line; the two link lines; a blank line; the channel and subscribe lines; a blank line; the hashtags line. **No chapter timestamps** (no `00:00 Verse 1 ...` lines): the user does not want lyric timing in the upload text. The two link lines and the two channel lines are each a pair with a blank line between the pairs:

```
Watch the full song: {FULL_VIDEO_URL}
Watch the Shorts: {SHORT_URL}

More story songs: https://www.youtube.com/@InkOfBallads
Subscribe: https://www.youtube.com/channel/UChThLWqUGxCJsx-TYefVNlw?sub_confirmation=1
```

  (`More songs:` instead of `More story songs:` for a personal lyric.) Both link lines go in every description, so after uploading the user pastes the same two links into the same two placeholders everywhere and cannot put one in the wrong place, even though each video then also links to itself. Never drop either line.
- **The Short uses the regular video's description**, word for word: the user pastes the same description into both. So `short.description` is a copy of `normal.description`, and `short.hashtags` a copy of `normal.hashtags` (no separate `#Shorts`: YouTube files the upload as a Short anyway).
- **Tags**: fill the 500-character Tags box (the upload text counts it the way YouTube does: quotes around tags with spaces, plus commas) to just under 500, but only with tags that truly describe the song: its title and title variants ("<title> song", "<title> lyrics"), the source work, its characters, places and author, the story's themes, the genre and instruments, "Full Song", "story song"/"ballad"/"love song" as fits, and InkOfBallads. Never pad with unrelated popular tags or other artists' names: YouTube treats misleading tags as spam, and tags count for little in search anyway, so the user should not expect "all possible tags". The Short gets the same tags, plus `Shorts` if it still fits.
- **Every tag is also in the description, as a hashtag** (the user asked for this on 2026-11-17). Build the `hashtags` list (and the description's last line, the same hashtags separated by spaces) from the song's own hashtags first, since YouTube shows the first three above the title, then one hashtag per regular-video tag that is not already there: words joined in CamelCase, letters and digits only (`Pied Piper of Hamelin song` → `#PiedPiperOfHamelinSong`), duplicates dropped ignoring case. Never paste the tags into the description as a plain word list: YouTube's spam policy counts that as keyword stuffing, which can hide or remove the video; hashtags are the allowed form. Keep the total under 60, because YouTube ignores every hashtag on a video that has more than 60 (Pay the Piper has 31). The Short's extra `Shorts` tag does not get a hashtag, since the description is shared.

When a song's `youtube` block already exists but lacks either link line (`Watch the full song` / `Watch the Shorts`), add just the missing lines (and `short_url` under `links`) in those places, changing nothing else in the block, and say so in the report; this is the one change allowed to an existing block without asking. Do it only for the song folder you are working on: never go through other songs' JSON files (the user stopped that once). The other house rules above (title, no chapters, shared description, tags) apply to blocks you write; bring an older block in line with them only when the user asks for that song. Edit the JSON as text (insert lines) rather than loading and re-dumping it, unless the file is already exactly in `json.dumps(indent=2, ensure_ascii=False)` layout (check by re-dumping and comparing), so the rest of the file keeps its formatting.
- Base everything on what the song JSON says (title, `plot_summary`, `source`, lyrics, `channel_reason`, `safety_check`); invent no facts. `made_for_kids` is `no` unless the song is clearly aimed at children (then say what that switches off).

Add the block with a short Python script that loads the JSON, sets `version["youtube"]`, and writes it back with `indent=2, ensure_ascii=False`, changing nothing else. Copy the JSON to `<scratchpad>` first, and afterwards check that only the `youtube` key was added (compare the old and new JSON with the `youtube` key removed). Never replace a `youtube` block that is already there unless the user asks; to improve one, change only what they asked for.

**8b. Write the upload text** with the program, as plain text with no JSON quotes, brackets or escapes, so the user can paste each part straight into YouTube Studio:

```
"<program>/.venv/Scripts/b2s-video.exe" upload-text --song "<json>" --out "<folder>/out/<folder>-youtube.txt"
```

This is the program's `upload-text` command (`--out` defaults to that same path; `--version` picks a version when several have a `youtube` block). The file has a section for the regular video and one for the Short, each with the title, description, tags (comma-separated for the Tags box), thumbnail text, pinned comment and Studio settings, and character counts against YouTube's limits. It also reads the older layout (description and tags shared at the top of the block) and the upload skill's standalone `<folder>.metadata.json`. It prints any `{PLACEHOLDER}` still in the text (such as `{FULL_VIDEO_URL}` and `{SHORT_URL}`); tell the user to fill those in after uploading (best in the JSON). Links the user pasted by hand over a placeholder in an earlier `.txt` are kept when it is made again, and it says so. It replaces a file it wrote before, but refuses any other file at that path without `--force`.

Run it again **whenever the `youtube` block changes** (a new description, more tags, a new title), including when the video-upload-metadata skill updated the JSON in a turn without any video work. The JSON stays the source: change the text there, never only in the `.txt`. If the user only wants the upload text for a song (no video work), do 8a and 8b on their own.

### 9. Check and report

Grab a few frames to confirm what you made (the cover with the logo, a lyric page with watermark and quill tab, The End page with the logo and the circled "Like & Subscribe"): `ffmpeg -v error -y -i <video> -vf "select='eq(n\,30)+eq(n\,450)',scale=300:-1,tile=2x1" -frames:v 1 <png>` and Read the image. Do the same for the 16:9 file (scale to 480 wide) and check that the notebook fills the height, a little left of centre, on an even background with the logo on the right. For the Short, grab a frame 4 s before the end (no pill) and one 0.5 s before the end (the pill fully shown under the notebook). Then tell the user, in plain words:

- each file's path (as a clickable link) and length,
- the upload text file and any placeholders left in it, and, if you wrote the `youtube` block, its titles and the made-for-kids and AI answers you chose, so the user can change them,
- that the 16:9 file and the 16:9 thumbnail are for the regular YouTube upload, and the Short (or 9:16) with the 9:16 thumbnail for Shorts, Reels and TikTok,
- that the Short's pill only works once its **Related video** is set: after the regular video is public, YouTube Studio > Content > Shorts > the Short > Details > Related video, pick the regular video (it can be set or changed after publishing),
- which page times you changed and why ("page 5 turned during 'merry and strong'; moved to 1:00.0"),
- anything still uncertain (lines Whisper did not hear, tight gaps),
- that you checked frames and timings but did not watch or listen to the whole video, unless you did.

## Things to avoid

- Changing lyric wording or the song JSON. The video shows the lyrics exactly as written; if a line looks wrong, tell the user. The only changes allowed are adding a missing `youtube` block and adding the missing "Watch the full song" and "Watch the Shorts" link lines to an existing one, for the song being worked on (both step 8a).
- Uploading or publishing anything. These are local files; uploading is the user's step.
- Overwriting the user's originals: their MP3, JSON, a hand-made `turns.txt`, or older videos that are not this skill's outputs. Earlier files from this workflow (same names in `out\`) may be replaced.
- Editing the program itself during a video request. If the template needs a change (layout, new option), say so, show a mock-up still first, and change it only when the user agrees; the program has its own tests (`program/.venv/Scripts/python.exe -m pytest` from `program`).

## If the user asks how to run it themselves

Give them the commands from steps 2 to 8 with their folder's real file names filled in, one command per code block, and point them to `program\README.md` for every option.
