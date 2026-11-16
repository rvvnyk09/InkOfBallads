---
name: video-upload-metadata
description: Generate ready-to-paste upload metadata for a video on YouTube (long-form and Shorts), TikTok and Instagram Reels — titles, descriptions, tags, hashtags, captions, chapters, thumbnail text, category, audience/made-for-kids setting, AI-content disclosure and posting checklist. Use whenever the user wants to upload, publish or post a video and asks for a title, description, tags, hashtags, caption, SEO, keywords, or "metadata", or hands over a script, lyrics, transcript, video file name or topic and asks what to put in the upload form. Also use for rewriting or optimizing existing titles/descriptions/tags for these platforms.
---

# Video upload metadata

Produce everything needed to fill in the upload forms on YouTube, TikTok and Instagram for one video, tailored to each platform's limits and audience behaviour.

Platform limits and field lists live in `references/platforms.md`. Read it before writing, and respect every hard limit there — count characters, don't estimate.

## 1. Gather inputs

Work from whatever the user gave you: a topic, script, lyrics, transcript, file name, an existing JSON (e.g. song/story output from another skill), or a folder. If a transcript or script file is mentioned, read it. Extract or ask for only what is missing and actually matters:

| Input | Default if not given |
|---|---|
| What the video is about (topic, story, key moments) | Required — ask if you truly have nothing |
| Platforms | All: YouTube long-form or Shorts (infer from length/orientation), TikTok, Instagram Reels |
| Duration and orientation | Vertical ≤ 3 min → Shorts/TikTok/Reels; otherwise YouTube long-form |
| Audience | General. If the content is aimed at children, set made-for-kids (see below) |
| Language | Language of the source material |
| Channel name, links, socials, call to action | Leave clearly marked placeholders like `[CHANNEL LINK]` |
| Timestamps / sections | Build chapters only if real timestamps are given or derivable; never invent times |
| AI involvement (AI music, voice, visuals) | Ask if unclear — it drives the disclosure fields |

Don't stall on optional items: produce the output with placeholders and list what to fill in.

## 2. Research the angle (briefly)

- Identify the 3–5 phrases a viewer would actually type or search for (primary keyword first). Prefer specific phrases ("Little Red Riding Hood song for kids") over generic ones ("song").
- Pick the hook: the single most curiosity-provoking or emotional element of the video.
- If web search is available and the user wants trend-aware hashtags, check current trending tags for the niche; otherwise use evergreen niche tags and say so.

## 3. Write per platform

Write natively for each platform — don't paste the same text everywhere.

**YouTube (long-form)**
- Title: primary keyword near the front, hook, ≤ 70 chars preferred (hard limit 100). Give 3 options, best first. No clickbait the video doesn't deliver; no all-caps titles.
- Description: first 2 lines (~150 chars) carry the hook + keyword since they show above "more". Then a short summary, chapters (if available), credits/sources (e.g. public-domain source text, AI music tool), links/CTA placeholders, then 3–5 hashtags on the last line (the first 3 appear above the title).
- Tags: 10–20, most specific first, include common misspellings/variants only when realistic, total ≤ 500 chars.
- Category, language, made-for-kids, altered/synthetic content answer, license, playlist suggestion.
- Thumbnail: 3 text options of 2–4 words each plus a one-line visual concept.

**YouTube Shorts**: title ≤ 60 chars with the hook up front; short description (1–3 lines + 3 hashtags, may include `#Shorts`); tags still allowed. Suggest a related long-form video to link if one exists.

**TikTok**: caption that starts with a hook line, conversational, 1–3 short sentences, then 3–5 hashtags mixing 1–2 broad and 2–3 niche. Suggest on-screen text for the first 2 seconds, cover-frame text, and whether to label as AI-generated.

**Instagram Reels**: first ~125 chars must work alone (hook + keyword, it's what shows before "more"). Then a short body, CTA (save/share/comment prompt), and hashtags within the current cap. Provide alt text (plain description of what's on screen), on-screen cover text, and suggested audio note, location/collaborator placeholders, and the AI-label setting.

## 4. Safety and policy checks

Always check and report briefly:
- **Kids content**: if aimed at children, YouTube "made for kids" = Yes (comments and personalised ads get disabled — tell the user). TikTok and Instagram require users 13+, so phrase captions for parents/families rather than addressing young kids directly.
- **AI disclosure**: realistic AI-generated or altered people, voices, places or events → disclose (YouTube "altered or synthetic content", TikTok "AI-generated content" toggle, Instagram "AI info" label). Obviously animated/fantastical content generally doesn't need YouTube's disclosure, but say what you assumed.
- **Copyright**: credit public-domain sources; flag third-party music, clips or characters the user may not have rights to. Don't use trademarked names in tags unless the video is actually about them.
- **No misleading metadata**: tags and hashtags must relate to the video (irrelevant tags violate YouTube spam policy).

## 5. Output format

Reply with a Markdown section per platform in this order: YouTube (or Shorts), TikTok, Instagram — each with every field as a copy-ready code block so the user can paste it directly. Show the character count next to every length-limited field, e.g. `Title (58/100)`.

Then a **Checklist** section: placeholders to fill, settings to toggle, and any warnings from step 4.

If the user asks for a file, or there are several videos, also write a JSON file using this shape (one object per video):

```json
{
  "video": "file name or working title",
  "youtube": {
    "format": "long | shorts",
    "titles": ["...", "...", "..."],
    "description": "...",
    "tags": ["..."],
    "hashtags": ["#..."],
    "chapters": [{"time": "00:00", "label": "..."}],
    "category": "...",
    "language": "...",
    "made_for_kids": false,
    "altered_or_synthetic": false,
    "playlist": "...",
    "thumbnail_text": ["..."],
    "thumbnail_concept": "..."
  },
  "tiktok": {
    "caption": "...",
    "hashtags": ["#..."],
    "on_screen_hook": "...",
    "cover_text": "...",
    "ai_generated_label": false
  },
  "instagram": {
    "caption": "...",
    "hashtags": ["#..."],
    "alt_text": "...",
    "cover_text": "...",
    "ai_label": false,
    "collaborators": [],
    "location": null
  },
  "checklist": ["..."]
}
```

For a batch of videos, keep the tone and hashtag set consistent across the series, vary titles so they don't look duplicated, and suggest a playlist/series name.
