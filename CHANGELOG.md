# Changelog

All notable changes to joyboy are listed here, newest first.

## Unreleased

### Changed

- Added the skills.sh listing badge, discovery keywords and an explicit compatibility matrix.

## 1.1.0 - 2026-11-13

### Added

- **Website tours.** `film.site(url)` downloads a public web page once (a sharp image of the whole page, the page itself, and every heading, button, card, image and section with its words and position). Shots can then travel to an element, light it while the rest dims, label it, lift it off the page, click it with a cursor, or scroll, with matching sounds. The page's own colours and fonts are saved so the video can match the site. Public pages only; nothing is typed or submitted on the real site.
- **Supertonic voices.** An optional, more expressive voice-over engine that runs on the user's own computer. Ten voices (`F1`-`F5`, `M1`-`M5`), 31 languages, and `<laugh>`, `<sigh>` and `<breath>` tags inside a line. Used when a voice name matches or with `Film(tts="supertonic")`; the tags are removed from captions and from other engines. The voice model is about 385 MB and is downloaded on first use; its weights are under the OpenRAIL-M licence.
- `CHANGELOG.md`.

### Changed

- **Ambience is always subtle.** Background sound for a place (sea, rain, fire, wind and the rest) is now levelled to a quiet bed under the music, whatever the place, and drops further while someone speaks. `w.level` raises or lowers it (default 1.0, at most 2.0).

## 1.0.0 - 2026-11-13

First public release.

- Scene-based fast path: a short script of scenes becomes a finished MP4 with music, sound effects and narration, in tall, wide or square.
- Camera moves over stills, titles, kinetic words, quotes and lists that size themselves to fit.
- Counters and charts that draw themselves, library icons, and street maps from OpenStreetMap data.
- Real web pages captured and shown in a phone frame or a browser window; GSAP scenes captured frame by frame.
- Three kinds of 3D: GSS shapes, real model files with 67.js, and procedural worlds with talking characters.
- Generated music, ambience, a matching sound for what each scene shows, and voice-over with ElevenLabs, Piper or the system voice.
- One persistent workspace so tools are installed once, with a script kept beside every video.
- Showreel, seven chapter videos and 24 example videos, one per kind of video.
