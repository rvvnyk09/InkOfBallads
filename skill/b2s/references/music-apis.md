# Sending the JSON to music generators

Vendor terms and API shapes change quickly, so tell the user to confirm current docs and, above all, commercial-use and redistribution terms before building on any vendor. These notes come from a search done in October 2026, and commercial terms were not verified for any vendor.

## Preparing the lyrics

The song is the single entry in the `versions` array, and it has a `lyrics` array. Join its lines with line breaks into one text block before sending:

- Python: `v = data["versions"][0]; lyrics_text = "\n".join(v["lyrics"])`
- JavaScript: `const v = data.versions[0]; v.lyrics.join("\n")`

Section tags are already in the lyrics, in the style generators expect, such as `[Verse]` and `[Chorus]`. Some generators use lowercase tags (MiniMax shows `[verse]`), so lowercase them if needed. Support for uncommon tags varies, so test with a short song first.

## Field mapping

| Provider | `style_prompt` | `lyrics` | `title` | Notes |
|---|---|---|---|---|
| MusicGPT | `prompt` or `music_style` | `lyrics` | `title` | Closest one-to-one match. One page says single-song-per-generation is enterprise-only, so confirm the plan. |
| MiniMax Music (official) | `prompt` | `lyrics` | no obvious field | Keep the title in your own app. Its lyrics-generation endpoint returns a title and style tags, which resembles this JSON. |
| Suno via a third-party gateway (for example EvoLink) | `style` | `prompt` (appears to carry the lyrics in custom mode) | `title` | Custom mode needs style, title, and lyrics. No official public Suno API was found, so check the gateway's terms and reliability. |
| Creatify (wraps MiniMax) | `prompt` | `lyrics` | no obvious field | Exposes a text-to-music type. |
| YuE (open source) | style prompt | lyrics | not applicable | Self-hosted, so no per-song fees, but more setup. |

## Adapter pattern

Keep this JSON as the source of truth and write one small adapter function per provider that renames keys and joins the lyrics. That lets the app swap vendors as terms, price, and quality change.

## Before posting generated music

- Listen to the result for any melody that sounds like an existing song.
- Never put a real artist's name or a sound-alike request in `style_prompt`.
- Be careful with voice-cloning features, because voice likeness has its own legal exposure.
- Purely AI-generated lyrics and music have weak copyright protection. Human edits, records of drafts, branding, and watermarks are stronger protection than copyright alone.
