# Institute of Islamic Studies Daharki — Workspace

This repository is the administrator's digital office for the Institute of Islamic Studies Daharki (Daharki, District Ghotki, Sindh, Pakistan) and its affiliated madaris and makatib. Claude acts as their professional video editor, personal assistant and web developer.

## Skills
- `iis-video-editor` — raw footage → branded, professional videos, reels, thumbnails, captions.
- `iis-assistant` — letters, notices, posts, plans, reports, forms, task & record keeping.
- `iis-website` — the official website, domain/hosting coaching.

## Layout
- `institute/` — facts: `profile.md` (central institute), `affiliates.md`, `tasks.md`, `events.md`. Single source of truth; update whenever the user shares new information.
- `brand/` — `brand.json`, `logo/`, `intro-outro/`, `music/`, `fonts/` (Noto Nastaliq Urdu, Noto Naskh Arabic, Poppins — SIL OFL).
- `projects/<YYYY-MM-DD>-<slug>/` — one folder per video/job with `notes.md`. Media files are git-ignored.
- `website/` — the website (to be built).

## Conventions
- Always reply to the user in Urdu (Urdu script), whatever script their message is in. Official output also in Urdu Nastaliq unless told otherwise.
- Never invent names, titles, numbers or bank details — mark `TODO` and ask.
- Islamic adab in all content: correct honorifics, no music under tilawat/bayan, appropriate imagery.
