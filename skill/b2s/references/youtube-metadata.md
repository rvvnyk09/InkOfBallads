# YouTube metadata for each song

Fill the `youtube` block of the JSON for every song. The user uploads two videos per song: a **normal** (horizontal, full-length) video and a **short** (vertical clip, made by cutting the start of the normal video), so write one set of metadata for each.

## Channel details (update if they change)

- Channel name: InkOfBallads
- Handle link: https://www.youtube.com/@InkOfBallads
- Subscribe link: https://www.youtube.com/channel/UChThLWqUGxCJsx-TYefVNlw?sub_confirmation=1
- Channel tagline: Classic stories, retold as ballads.

## The `links` block

Put these in `youtube.links`, and build every description from them:

- `handle_url`, `subscribe_url`: the two channel links above.
- `full_video_url`: placeholder `{FULL_VIDEO_URL}` (the normal video, linked from the short).
- `playlist_url`: placeholder `{PLAYLIST_URL}` (optional).
- `next_video_url`: placeholder `{NEXT_VIDEO_URL}` (optional).
- `source_text_url`: placeholder `{SOURCE_TEXT_URL}`, a free copy of the original text (optional).

Never invent URLs. Keep placeholders until the user supplies the real link, and ask for it in chat.

## Rules

- **Exact title:** use the exact song title from the JSON in the video title and in any hook line. Never mix title variants (for example Two Hearts, Two Houses versus Two Houses, One Heart). If the title and a hook differ, ask the user which wording to use.
- **Never write "public domain"** in any title, description, tag, or hashtag. Keep the public-domain check in the JSON `source` block only. Use "classic literature" or "classic story" for tags.
- **AI line:** every description includes "AI-assisted music and lyrics."
- **Not affiliated:** every description says the song is an original song and not affiliated with any film, stage production, musical, or publisher that applies.
- Title: 100 characters at most, with about 60 to 70 shown in search, so put the searchable words first. A short's title shows about 40 characters in the shelf.
- Description: 5,000 characters at most, and the first line (about 157 characters) is the hook.
- Tags (normal video only): 500 characters in total including commas, and spaced tags count 2 extra. Only truthful tags, with no brand names borrowed from films. Include `InkOfBallads`. Use at most 15 tags, so every tag can also be written as a hashtag. Tags matter less than the title, thumbnail, and description.
- Hashtags: turn every tag into a hashtag (CamelCase, with no spaces or hyphens, for example "star-crossed lovers" becomes #StarCrossedLovers), list them in the `hashtags` field, and put them on the last line of the normal video's description. Put the three most important first, because the first three show above the title. Keep the total at 15 or fewer, because sources disagree on YouTube's limit and it may ignore all hashtags when there are too many. The short gets the best three plus #InkOfBallads and #StorySong, and optionally #Shorts (at most 6).
- Descriptions are arrays of lines in the JSON (one line per entry, an empty string for a blank line), like the lyrics. The caller joins them with line breaks.

## Normal video description (structure)

1. Hook (one or two sentences, within about 157 characters).
2. One paragraph on the story and who it's for. Mention the song length only if the user gives it.
3. Source line: "Based on the {legend or book} ({author}, {year}). Original song, not affiliated with any film or publisher. AI-assisted music and lyrics."
4. Call to action question ("What classic story should we turn into a song next? Comment below!").
5. Links: `More story songs: {handle_url}` and `Subscribe: {subscribe_url}`, plus optional playlist, next video, and source text lines when the user has them.
6. Hashtags: every tag as a hashtag, on the last line, best three first.

## Short description (structure)

1. Hook line.
2. `Watch the full song: {FULL_VIDEO_URL}`
3. Source line (same as above, kept short).
4. Call to action question.
5. Handle link and subscribe link.
6. Hashtags: the best three plus #InkOfBallads and #StorySong, and optionally #Shorts.

## Personal songs (the user's own lyrics)

When the song is the user's own lyrics (see "Your own lyrics" in `SKILL.md`), everything above applies, with these differences:

- `links`: leave out `source_text_url`, since there is no source text.
- Normal title: the exact song title first, then what kind of song it is in a few words, for example "Warmth on the Table | Feel-Good Thanksgiving Song" or "Your Eyes Feel Like Home | Sweet Love Song". Never call it a ballad of a story.
- Story paragraph: about the song's feeling, setting and message, from `plot_summary` and the lyrics. Describe the sound in plain words if it helps (for example "a vintage soul-pop song with warm bass and soft horns").
- Source line: "Original song. AI-assisted music and lyrics." The "not affiliated" sentence is only needed if the song mentions a film, show, brand or publisher.
- Call to action: a question about the song's theme (for example "Who will be at your table this Thanksgiving? Tell us in the comments!"), not "What classic story should we sing next?".
- Links: `More songs: {handle_url}` instead of `More story songs:`.
- Tags and hashtags: the title and its variants, the theme, occasion or season, the genre and mood, and `InkOfBallads`. No "classic story", "story song", "ballad" or "classic literature" tags. The short gets the best three plus #InkOfBallads and #OriginalSong (not #StorySong), and optionally #Shorts.
- `pinned_comment`: the same theme question plus the subscribe link.
- `playlist` (normal video): "Original Songs".

## Other fields

- `thumbnail_text` (normal video): the song title in capitals, 2 to 5 words, to put in large letters over the user's own artwork. Never use film imagery.
- `pinned_comment`: a question that invites a reply plus the subscribe link, for example "Which classic story should we sing next? Subscribe: {subscribe_url}".
- `studio_settings` (each video):
  - `made_for_kids`: "no" by default, and tell the user it must be set honestly (use "no" for anything with a tragic ending).
  - `ai_use_disclosure`: "answer the AI use question in YouTube Studio". The AI line in the description does not replace it.
  - `category`: "Music".
  - `language`: the language of the lyrics.
  - `playlist` (normal video only): the series playlist name, for example "Classic Ballads".

## Reminders for the user (say in chat)

- Replace every placeholder before publishing, and test the subscribe link while signed out.
- Answer the AI use question in Studio for each upload.
- Check the made-for-kids choice for each video.
