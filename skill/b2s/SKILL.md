---
name: "b2s"
description: Write original, family-safe song lyrics about public-domain books, stories, fairy tales, legends, plays, and historical events, returned as one structured JSON for a General Audience (GA) song (shared plot summary and source record, plus a title, channel reason, safety check, style prompt, and lyrics array), ready for AI music generators like Suno, MusicGPT, and MiniMax. Use this skill whenever the user asks for a song, lyrics, or a "song version" of a book, chapter, story, fairy tale, play, or event, mentions the Book-to-Song app or the General channel, or wants lyrics for an AI music generator, or asks to rewrite, soften, or check a song for all-audience suitability or copyright status. Also use it when the user names a movie or modern book and wants a song about it, because this skill handles redirecting to a public-domain alternative or the real history behind it. Also use it when the user pastes or supplies their own personal lyrics (an original song they wrote, with or without a story behind it) and wants them turned into the song JSON, a title, a style prompt, or YouTube details: the skill keeps their words as written and skips the public-domain steps.
---

# Book-to-Song

Turn a public-domain story into an original, entertaining song for a General Audience (GA), and return one JSON that a music-generation API can consume directly. Each story gets one GA song of about 2 to 2.5 minutes.

The songs are posted on the General channel (YouTube, Instagram, TikTok). Two things matter most: the song must be faithful to the story (accuracy is the product's edge), and it must be safe to post for everyone (no mature content, and no copied material).

## Workflow

If the user gives you **their own lyrics** instead of naming a story, follow "Your own lyrics" below instead of this workflow.

1. **Check the source.** Confirm the work is public domain (US rule of thumb: published in 1930 or earlier). If the user names a movie, a modern book, or anything still protected, do not write about its characters, plot, or lines. Tell them briefly why, then offer either a public-domain story with the same appeal or the real history behind it, and write that instead. When unsure about a work's status, read `references/public-domain.md`.
2. **Write a plot summary first**: five short bullets from the original work (or the stated chapter). It is the accuracy anchor. Every lyric line must be supportable by it, with no foreshadowing and no events from other chapters. Where versions of a tale differ (for example Grimm versus Perrault), pick one and name it in the `source.edition` field.
3. **Write the GA song** (see below).
4. **Run the safety check** on your draft. If anything is flagged, rewrite the lines before output, so `safety_check.passed` is true.
5. **Fill the `youtube` block** from `references/youtube-metadata.md`: the links, and a title, description, hashtags, pinned comment, and Studio settings for the normal video and for the short (plus tags and thumbnail text for the normal video).
6. **Return the JSON** in the template below.

## Your own lyrics

The user also writes personal songs: original lyrics of their own, often about feelings, family, or a season (for example *Your Eyes Feel Like Home* and *Warmth on the Table*). When they paste lyrics, or say the lyrics are their own or personal, the job is to package their song, not to write one.

1. **Keep their words exactly.** Copy every line as written, with the same wording, punctuation, and line order. Never rewrite, shorten, or "improve" a line in the JSON. The only change allowed is to the section tags: map each tag to the nearest allowed tag (`[Verse 1]` and `[Verse 2]` become `[Verse]`, `[Final Chorus]` becomes `[Chorus]`, `[Pre Chorus]` becomes `[Pre-chorus]`), put each tag in its own entry and an empty string between sections, and drop stray quotes and commas left over from pasting a JSON array. If a section has no tag, ask, or tag it by its role and say so. Suggestions for weak lines (meter, a forced rhyme, a line over about 35 characters that wraps on the 9:16 page, a section much longer than four lines that crowds one notebook page) go in the note after the JSON, as suggestions the user can take or leave.
2. **Skip the story steps.** There is no public-domain check, no plot summary from a book, and no accuracy check against a source.
3. **Check it is theirs.** If the lyrics closely match a well-known published song (a famous chorus, a recognisable run of lines), say so and do not package them until the user confirms they wrote them. Do not name or quote the other song beyond what is needed to point it out.
4. **Run the safety check** as usual, but on their words: list anything that would not suit a general audience in `safety_check.flags`, set `passed` to false if anything is flagged, and tell the user which lines and why. Do not rewrite their lines yourself; offer a softer wording in the note if they want one.
5. **Title.** Use the title the user gives. If there is none, suggest three to five short titles built from the hook or the chorus's strongest image, recommend one, and use it in the JSON while telling the user they can change it. A title of two to five words reads best on the notebook cover.
6. **Style.** Use the user's style prompt word for word if they give one. Otherwise choose one from the lyrics as described in Choosing the style.
7. **Fill the JSON** in the same template, with these differences:
   - `plot_summary`: three to five short bullets on what the song is about (who is singing, the setting, the feeling, the message), taken only from the lyrics. It feeds the YouTube description.
   - `source`: `"work": null` (the notebook cover then shows only the title, with no "after ..." line), `"author"`: the user's name if they gave one, otherwise "The user", `"edition": null`, `"first_published": null`, `"public_domain_basis"`: "Not applicable: the user's own original lyrics", `"based_on_modern_adaptation": false`, `"human_verified": false`.
   - `channel` stays "general", and `channel_reason` says in one sentence why the song suits everyone.
   - `youtube`: follow `references/youtube-metadata.md` with the personal-song differences listed there under "Personal songs".
8. **In conversation**, give a one-line note on what you changed (tags only) and any assumption (title, style), then the JSON, then short suggestions: the hook, two or three lines that may sing awkwardly, and anything flagged. Do not critique accuracy or sources, since there are none.

## The GA format

Write one song for a General Audience (GA): suitable for everyone, from children to adults. Depict what the story actually portrays, including danger, loss, or tragedy, told respectfully. Keep it non-graphic: no gore, no method details for killing or self-harm, no glorifying harm. Choose the style as described in Choosing the style. Write only the GA song and do not write a separate Kids version. If the user asks for a Kids version, tell them this skill is set to produce only the GA format.

## Never write

18+, mature, or restricted content: sexual content, graphic violence or gore, drug use, hate, or self-harm methods. If a story depends on these, soften it to suit a general audience or decline that story. Explain the limit in one sentence rather than lecturing.

## Songwriting craft

- **Original wording only.** Describe events in your own words. Do not quote or closely paraphrase the book's sentences, including famous dialogue. Do not imitate real artists by name or style.
- **Chorus pattern: a feeling, an everyday image, and a positive message.** For example, feeling small (feeling), a friend by your side (image), together we are strong (message). Concrete everyday images such as food, weather, home, and nature make songs memorable and easy to picture.
- **One repeatable hook line** in the chorus, short enough to chant. Hooks are what make clips shareable.
- **Chorus count is flexible.** By default use the chorus up to three times, spaced apart by verses or the bridge, and let the last chorus change a few lines to resolve the story while keeping the hook line. If the user gives a chorus limit, follow it. The song's shape can change with its style, for example Verse, Chorus, Verse, Chorus, Bridge, Chorus (24 lines). Mention if the hook arrives late.
- **Vivid, specific lyrics.** Use concrete images from the story (places, objects, weather, actions) and longer, flowing lines of about 10 to 16 syllables, not short punchy filler lines. Specific scenes make a song richer and keep its pace feeling full.
- **Vocals starting by 3 seconds is the goal.** Start the lyrics directly with `[Verse]` (no `[Intro]` tag unless the user asks) and make the first line a sung line. Do not rely on the style text to control the intro: the music app may rewrite the style prompt and drop timing words, so timing requests there are not dependable. Tell the user to check when the vocals start on the first take. If they come in late, they can trim the start, for example `ffmpeg -i song.mp3 -ss 8.5 -af "afade=t=in:st=0:d=0.4" -c:a libmp3lame -q:a 2 song_trim.mp3` (set `-ss` to about 2.5 seconds before the first sung word), and they should measure page-turn times after trimming.
- **Clean ending.** Likewise, do not rely on the style text for a clean ending. If a generated song runs long or fades slowly, the user can trim it with a fade-out, for example `ffmpeg -i song.mp3 -t 145 -af "afade=t=out:st=142:d=3" -c:a libmp3lame -q:a 2 song_short.mp3`.
- **Rhyme and meter should be singable** at the chosen tempo. Avoid filler lines that rhyme but mean nothing, and keep bridges rhymed.
- **Keep plot order.** Chorus lines should not jump ahead of the verses.
- **Length: target 2 to 2.5 minutes.** Use about four lines per section and no more than 28 lines (7 sections) per song. A line takes about two bars, roughly 4 to 4.4 seconds at 110 to 120 BPM (about 4.8 seconds at 100 BPM), so the line budget is about (target seconds minus 15) divided by seconds per line. Generators often add pauses, instrumental breaks, and a long outro, so lyrics that look short on paper can still run past 3 minutes at a slow tempo. Longer lines take longer to sing, so aim for about 24 lines when the lines are long.
- **Long or episodic works** (a whole novel, a long epic): write a highlights song with at most one line per episode, or suggest one chapter per song, which gives each song room and makes it more accurate.
- **Section tags** use only the tags below, in square brackets, spelled exactly as shown, with no numbers or modifiers: `[Intro]`, `[Verse]`, `[Pre-chorus]`, `[Chorus]`, `[Hook]`, `[Drop]`, `[Bridge]`, `[Solo]`, `[Build-up]`, `[Instrumental]`, `[Breakdown]`, `[Break]`, `[Interlude]`, `[Outro]`. These are the tags the music tool's lyrics editor offers, so never invent others (no `[Verse 1]`, `[Final Chorus]`, or `[Spoken]`). Write `[Verse]` for every verse and `[Chorus]` for the final chorus too. Music generators read the tag as a section type, not an order.

## Choosing the style

There is no stock sound. Let the lyrics drive the style, with one exception for tragic or serious stories, described below. After writing the lyrics, read them back and note their story, setting, emotional arc, imagery, the pace and length of the lines, and the feeling of the chorus. From that, name the genre, two to four instruments, one rhythm cue, and the vocal character that best fit those lyrics, and keep the style prompt short and simple.

- **Draw on the lyrics.** Take instruments, rhythm, and vocal character from what the lyrics describe and how they feel. A barnyard tale, a royal court, a sea voyage, and a mystery should not end up with the same sound.
- **Each song gets its own style.** Do not reuse a style from an earlier song unless the lyrics call for it.
- **Use plain, direct names** for genres, instruments, rhythms, and vocals, such as folk, pop, funk, acoustic guitar, upright bass, hand claps, and female vocal.
- **Tragic or serious stories use the bittersweet ballad approach.** When the story is a tragedy, a tragic love story, or a solemn historical event (for example Romeo and Juliet or the sinking of the Titanic), write it the way the earlier *Two Hearts, Two Houses* and *Titanic* songs were written: a respectful storytelling voice, emotional but non-graphic lyrics, a repeated hook that carries the loss and the love, and a bittersweet acoustic ballad style with fingerpicked guitar, piano, and cello, restrained verses that build toward the chorus, and a steady mid-tempo feel. For love stories use male and female voices trading lines, and for events use one warm lead voice with quiet harmonies on the chorus. For this family of songs only, a tempo phrase such as steady mid-tempo is allowed in the style prompt. Examples the user liked: `soft sweet bittersweet acoustic ballad, fingerpicked acoustic guitar, gentle piano, expressive cello, steady mid-tempo 95 BPM, intimate female and male voices trading lines, warm blended harmonies on choruses` (tragic romance) and `solemn soft folk ballad, acoustic guitar, gentle piano and cello, steady mid-tempo around 95 BPM, warm male lead vocal, quiet harmonies on the chorus` (historical tragedy). For these songs, keep lines plain and about 9 to 13 syllables, in rhymed couplets, in the 28-line shape Verse, Chorus, Verse, Chorus, Bridge, Verse, Chorus, with the last chorus changed to resolve the story, as in `references/reference-songs.md`, which holds the two songs the user called masterpieces. Use this approach only when the story is apt, and let the lyrics drive the style for every other story.
- **Leave tempo and timing words out by default** (except for the ballad approach above). The music app may rewrite the style prompt and drop or change timing words, and tempo numbers have come out well off (a request for 112 BPM produced about 89 and about 129). Add a tempo word or number only if the user asks for one.
- **Check the style the app actually used.** Tell the user to compare it with the style you wrote, since it may differ.
- Never name real artists. If the user gives a genre, tone, or tempo in the request, follow it.

## Output template

Return exactly this shape. Each `lyrics` value is an array with one line per entry, the section tag in its own entry, and an empty string between sections. Never use `\n` inside the lyrics, because escaped line breaks make the JSON hard to read and edit. A music API usually wants one text block, so the caller joins the array with line breaks.

```json
{
  "plot_summary": ["", "", "", "", ""],
  "source": {
    "work": "",
    "author": "",
    "edition": "",
    "first_published": 0,
    "public_domain_basis": "",
    "based_on_modern_adaptation": false,
    "human_verified": false
  },
  "versions": [
    {
      "channel": "general",
      "title": "",
      "channel_reason": "",
      "safety_check": { "passed": true, "flags": [] },
      "style_prompt": "",
      "lyrics": ["[Verse]", "...", "", "[Chorus]", "..."],
      "youtube": {
        "links": {
          "handle_url": "https://www.youtube.com/@InkOfBallads",
          "subscribe_url": "https://www.youtube.com/channel/UChThLWqUGxCJsx-TYefVNlw?sub_confirmation=1",
          "full_video_url": "{FULL_VIDEO_URL}",
          "playlist_url": "{PLAYLIST_URL}",
          "next_video_url": "{NEXT_VIDEO_URL}",
          "source_text_url": "{SOURCE_TEXT_URL}"
        },
        "normal": {
          "title": "",
          "description": ["hook line", "", "story paragraph", "", "source line", "", "call to action", "", "links", "", "#Tag1 #Tag2 #Tag3 (every tag as a hashtag, 15 at most)"],
          "tags": ["", ""],
          "hashtags": ["#Tag1", "#Tag2", "#Tag3"],
          "thumbnail_text": "",
          "pinned_comment": "",
          "studio_settings": {
            "made_for_kids": "no",
            "ai_use_disclosure": "answer the AI use question in YouTube Studio",
            "category": "Music",
            "language": "English",
            "playlist": "Classic Ballads"
          }
        },
        "short": {
          "title": "",
          "description": ["hook line", "Watch the full song: {FULL_VIDEO_URL}", "", "source line", "", "call to action", "links", "", "#Tag1 #Tag2 #Tag3 #InkOfBallads #StorySong #Shorts"],
          "hashtags": ["#Tag1", "#Tag2", "#Tag3", "#InkOfBallads", "#StorySong", "#Shorts"],
          "pinned_comment": "",
          "studio_settings": {
            "made_for_kids": "no",
            "ai_use_disclosure": "answer the AI use question in YouTube Studio",
            "category": "Music",
            "language": "English"
          }
        }
      }
    }
  ]
}
```

Field notes:

- `versions`: an array holding one object, the GA song, with `channel` set to "general". The array is kept so downstream tools that read `versions` keep working.
- `youtube`: everything needed to publish the two videos for each song (a normal full-length video and a short): the channel `links`, and for each video a title, a description (an array of lines), hashtags (the normal video uses every tag as a hashtag, 15 at most, best three first), a pinned comment, and Studio settings, plus tags and thumbnail text for the normal video. Follow `references/youtube-metadata.md` for the channel details, structure, limits, rules, and placeholders. Use the exact song title in titles and hooks, never write "public domain" anywhere in the youtube block, include "AI-assisted music and lyrics." in every description, never use `\n`, never invent URLs, and ask the user for any missing link in chat.
- `channel_reason`: one sentence on why this song suits a general audience, and what was softened or left out if anything.
- `safety_check.flags`: list any line or idea you softened or considered risky. It should be empty when nothing was flagged.
- `style_prompt`: driven by the lyrics (see Choosing the style): short and simple, with the genre, two to four named instruments, a rhythm cue, and the vocal character. Leave out BPM and timing words by default. Never name real artists.
- `source`: record the edition used and why it is public domain. For a historical event, set `author` to "Not applicable (facts from the public historical record)" and `first_published` to `null`. Always leave `human_verified` false, because a person must confirm legal status; you cannot.
- Use plain apostrophes and avoid quotation marks inside lyrics lines when you can, to keep the JSON clean. If a line needs a quote, escape it as `\"`.

## In conversation versus in a pipeline

- **In conversation** (the default): give a one-line note on any assumption (genre or tone), then the JSON, then a short critique: how accurate it is, the hook, anything softened or left out, two or three weak spots, and a source caution (for example adaptations to avoid). End with one short offer for a next step.
- **In a pipeline** or when the user asks for JSON only: output only the JSON object, with no other text.

## Examples

**A dark tale.** Request: "Hansel and Gretel." The GA song keeps the pebbles, the crumbs, the gingerbread house, the witch's plan to eat Hansel, and Gretel's cleverness and the witch's defeat as the Grimm tale tells it, told without graphic detail.

**Redirect, copyrighted film.** Request: "Write one for the Notebook movie." The film and the novel are protected, so do not retell their characters or plot. Say so in a sentence, then write a GA song about a public-domain story with the same appeal (for example Austen's *Persuasion* for a lost love found again), and explain the swap in one line.

**Redirect, film about real history.** Request: "Write one for Titanic movie." The film is protected, but the 1912 sinking is history and facts are not copyrightable. Write about the real events only, using none of the film's invented characters, scenes, or lines, and mark `source.work` as the historical event. Keep it respectful and non-graphic.

## Reference files

- `references/public-domain.md`: how to judge public-domain status, adaptation and translation watch-outs, and stories that are safe to use. Read it when the user names an unfamiliar work, a translation, or a borderline date.
- `references/reference-songs.md`: the Titanic and Two Hearts, Two Houses songs, with what they share. Read it before writing any tragedy, tragic love story, or solemn historical event.
- `references/youtube-metadata.md`: the channel details, the `links` block, description structures, tag and hashtag rules, other fields, and placeholders for the `youtube` block. Read it every time you write a song and follow it exactly.
- `references/music-apis.md`: how the JSON fields map to music-generation APIs. Read it when the user asks about sending the output to a generator or writing an adapter.
