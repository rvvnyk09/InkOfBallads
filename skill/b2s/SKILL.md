---
name: b2s
description: Write original, family-safe song lyrics about public-domain books, stories, fairy tales, legends, plays, and historical events, returned as structured JSON (title, channel, plot summary, safety check, style prompt, lyrics array, source record) ready for AI music generators like Suno, MusicGPT, and MiniMax. Use this skill whenever the user asks for a song, lyrics, or a "song version" of a book, chapter, story, fairy tale, play, or event, mentions the Book-to-Song app, a Kids channel or General channel, or lyrics for an AI music generator, or asks to rewrite, soften, or check a song for all-audience suitability or copyright status. Also use it when the user names a movie or modern book and wants a song about it, because this skill handles redirecting to a public-domain alternative or the real history behind it.
---

# Book-to-Song

Turn a public-domain story into an original, entertaining, all-audience song, and return it as JSON that a music-generation API can consume directly.

The songs are posted on a Kids channel and a General channel (YouTube, Instagram, TikTok). Two things matter most: the song must be faithful to the story (accuracy is the product's edge), and it must be safe to post (no mature content, and no copied material).

## Workflow

1. **Check the source.** Confirm the work is public domain (US rule of thumb: published in 1930 or earlier). If the user names a movie, a modern book, or anything still protected, do not write about its characters, plot, or lines. Tell them briefly why, then offer either a public-domain story with the same appeal or the real history behind it, and write that instead. When unsure about a work's status, read `references/public-domain.md`.
2. **Write a plot summary first**: five short bullets from the original work (or the stated chapter). This is the accuracy anchor. Every lyric line must be supportable by it, with no foreshadowing and no events from other chapters. Where versions of a tale differ (for example Grimm versus Perrault), pick one and name it in the `source.edition` field.
3. **Choose the channel** (see below).
4. **Write the lyrics** using the craft rules below.
5. **Run the safety check** on your own draft. If anything is flagged, rewrite the lines before output, so `safety_check.passed` is true.
6. **Return the JSON** in the template below.

## Channels

Each song goes to exactly one channel. A song never appears on both, because the Kids channel has stricter platform rules (for example YouTube's made-for-kids settings).

- **kids**: for ages 2 to about 8. Short words, simple rhymes, repetition. No death, weapons, or scary peril. Soften dark plot points gently while keeping the story's outcome (a witch's spell is broken instead of a witch being killed). Choose kids only if the whole story can be told this way; if softening would gut the story, choose general instead.
- **general**: for everyone. Depict what the story actually portrays, including danger, loss, or tragedy, told respectfully. Keep it non-graphic: no gore, no method details for killing or self-harm, no glorifying harm.

If the user asks for a specific channel, honor it, but if the story cannot honestly fit the kids channel, say so and offer the general version.

## Never write

18+, mature, or restricted content: sexual content, graphic violence or gore, drug use, hate, or self-harm methods. If a story depends on these, soften it to the level of the channel or decline that story. Explain the limit in one sentence rather than lecturing.

## Songwriting craft

- **Original wording only.** Describe events in your own words. Do not quote or closely paraphrase the book's sentences, including famous dialogue. Do not imitate real artists by name or style.
- **Chorus pattern: a feeling, an everyday image, and a positive message.** For example, feeling small (feeling), a friend by your side (image), together we are strong (message). Concrete everyday images such as food, weather, home, and nature make songs memorable and kid-friendly.
- **One repeatable hook line** in the chorus, short enough to chant. Hooks are what make clips shareable.
- **Keep the final chorus close to the earlier ones.** Let it resolve the story, but keep the hook intact so it stays repeatable.
- **Rhyme and meter should be singable** at the chosen tempo. Avoid filler lines that rhyme but mean nothing, and keep bridges rhymed.
- **Keep plot order.** Chorus lines should not jump ahead of the verses.
- **Length:** singable in 60 to 90 seconds, about four lines per section.
- **Long or episodic works** (a whole novel, a long epic): write a highlights song with at most one line per episode, or suggest one chapter per song, which gives each song room and makes it more accurate.
- **Section tags** use only the tags below, in square brackets, spelled exactly as shown, with no numbers or modifiers: `[Intro]`, `[Verse]`, `[Pre-chorus]`, `[Chorus]`, `[Hook]`, `[Drop]`, `[Bridge]`, `[Solo]`, `[Build-up]`, `[Instrumental]`, `[Breakdown]`, `[Break]`, `[Interlude]`, `[Outro]`. These are the tags the music tool's lyrics editor offers, so never invent others (no `[Verse 1]`, `[Final Chorus]`, or `[Spoken]`). Write `[Verse]` for every verse and `[Chorus]` for the final chorus too. Music generators read the tag as a section type, not an order.
- **Defaults:** soft, sweet, mid-tempo (about 95 to 100 BPM, not slow and not fast) unless the user gives a genre, tone, or tempo. A funny tone leans on wit and exaggeration; a serious tone leans on emotion and stakes. Put the tempo number and a plain description in `style_prompt`, because generators respond better to both than to "medium" alone.

## Output template

Return exactly this shape. The `lyrics` value is an array with one line per entry, the section tag in its own entry, and an empty string between sections. Never use `\n` inside the lyrics, because escaped line breaks make the JSON hard to read and edit. A music API usually wants one text block, so the caller joins the array with line breaks.

```json
{
  "title": "",
  "channel": "kids | general",
  "channel_reason": "",
  "plot_summary": ["", "", "", "", ""],
  "safety_check": { "passed": true, "flags": [] },
  "style_prompt": "",
  "lyrics": [
    "[Verse]",
    "...",
    "",
    "[Chorus]",
    "..."
  ],
  "source": {
    "work": "",
    "author": "",
    "edition": "",
    "first_published": 0,
    "public_domain_basis": "",
    "based_on_modern_adaptation": false,
    "human_verified": false
  }
}
```

Field notes:

- `channel_reason`: one sentence on why this channel, and what was softened if anything.
- `safety_check.flags`: list any line or idea you softened or considered risky. It should be empty when nothing was flagged.
- `style_prompt`: genre, instruments, tempo with a number, vocal style, and what the chorus should feel like. Never name real artists.
- `source`: record the edition used and why it is public domain. For a historical event, set `author` to "Not applicable (facts from the public historical record)" and `first_published` to `null`. Always leave `human_verified` false, because a person must confirm legal status; you cannot.
- Use plain apostrophes and avoid quotation marks inside lyrics lines when you can, to keep the JSON clean. If a line needs a quote, escape it as `\"`.

## In conversation versus in a pipeline

- **In conversation** (the default): give a one-line note on any assumption (channel, genre, tone), then the JSON, then a short critique: how accurate it is, the hook, two or three weak spots, and a source caution (for example adaptations to avoid). End with one short offer for a next step.
- **In a pipeline** or when the user asks for JSON only: output only the JSON object, with no other text.

## Examples

**Redirect, copyrighted film.** Request: "Write one for the Notebook movie." The film and the novel are protected, so do not retell their characters or plot. Say so in a sentence, then write a song about a public-domain story with the same appeal (for example Austen's *Persuasion* for a lost love found again), and explain the swap in one line.

**Redirect, film about real history.** Request: "Write one for Titanic movie." The film is protected, but the 1912 sinking is history and facts are not copyrightable. Write about the real events only, using none of the film's invented characters, scenes, or lines, and mark `source.work` as the historical event.

**Softening for the Kids channel.** Request: Hansel and Gretel for kids. Keep the pebbles, the crumbs, the gingerbread house, and Gretel's cleverness; turn the witch's defeat into a broken spell; skip the oven and the cooking. State that it is a retelling in `channel_reason`.

## Lyric video (b2s-video notebook template)

The JSON also feeds the b2s-video lyric-video tool, whose default look is a purple spiral notebook (`notebook.html`). Nothing in the output template changes for it, but it helps to know what it uses:

- **`title`**: the cover title. **`source.work`**: the cover line "after {work}". The cover also shows "Singing Notebook", a music note, and the channel name the user gives the tool (or "songs & stories").
- **`source.author` is not shown**: the notebook cover has no author line. Still fill it in for the source record.
- **`lyrics`**: each `[Tag]` section becomes one ruled notebook page, and the page turns are timed per section. Tags are never shown on the page; they only decide the page breaks, so a very long section crowds one page.
- **Line length**: in 9:16 (Shorts, Reels, TikTok) the handwriting is large, so lines over about 35 characters wrap onto a second ruled line. Shorter lines read better.
- Not used by the video: `channel` (it no longer picks the look), `channel_reason`, `plot_summary`, `safety_check`, `style_prompt`, and the rest of `source`.

## Reference files

- `references/public-domain.md`: how to judge public-domain status, adaptation and translation watch-outs, and stories that are safe to use. Read it when the user names an unfamiliar work, a translation, or a borderline date.
- `references/music-apis.md`: how the JSON fields map to music-generation APIs. Read it when the user asks about sending the output to a generator or writing an adapter.
