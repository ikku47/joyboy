# Changelog

All notable changes to joyboy are listed here, newest first.

## Unreleased

## 2.0.0 - 2026-11-14

### Added

- **Styles**: `Film(style=...)` with 49 mediums in six families (`references/styles.md`), each setting theme, look, grade, music, sound bed and scene mix.
- **Looks** (`looks.py`): riso, halftone, dither, engrave, bands, duotone, thermal, xray, ascii, film, cel, tiltshift as `fx=`; nine new themes; scenes `write`, `sketch`, `stamp`.
- **Foley and beds** (`foley.py`): 18 material sounds and 5 beds (`Film(bed=...)`); six new music genres (chiptune, jazz, mallets, citypop, counterpoint, roomtone).
- **Mastering and checks**: two-pass loudness to -14 LUFS with an oversampled limiter, encoder grain, bitrate cap; render prints `camera:`, `reading:`, `audio:`, `master:` checks.
- **3D**: at least four camera angles for 3D films; Blender models pass a 12-point QA and a multi-angle coverage sheet before they are registered.
- **Directing guide** (`references/directing.md`) and a treatment step in the plan; `imagegen.py` for consistent model-made pictures (asks first).
- Inspired by studying lemomo-ai/lemo-opuscar; nothing copied (its docs and prompts are CC BY-NC).
- **Matching a reference exactly**: `Film(exact=True)` (exact scene lengths, no beat snapping or fades), `voice_as=` (a voice per scene, one per character), and `refscan.py check` now skips the tempo score when the reference audio is speech, not music. A 56 second, 42-shot reference skit was recreated at 89/100 (41 of 41 cuts matched).
- **Skit v2**: a wide desk view with a monitor, a recolourable terminal bot with a face symbol, a desk paper, phone banners with a reply, eyelids, typing shake, dimmable rooms, caption windows, slices of one long shot; plus UI cards for it (`pip_done`, `pip_slider`, `pip_brand`, `pip_templates` with scripted flips and flicker, `pip_wall`, `pip_seq`).
- **A gated workflow** (`references/workflow.md`, summarised at the top of SKILL.md): setup and read everything, brief, research what is working now (`ig-viral`, Agent Reach), measure any reference, match every beat against the catalog, make what is missing instead of settling, check variety, and only then write the script. `plan.py` creates `plan.md` and checks that sections 1 to 6 are filled before the script; a render prints the plan's status.
- **Toolkit catalog** (`catalog.py`): everything the toolkit can do (scenes, themes, genres, looks, grades, effects, camera moves, transitions, sounds, saved assets) built from the code itself into `CATALOG.md`, with `catalog.py find "what the beat needs"` for the match step; no match means a gap.
- **Reference accuracy** (`refscan.py`): measures a reference video (shots, exact cut times, colours per shot, camera movement, tempo, loudness), writes a contact sheet, a table to describe every shot, and a timing skeleton; `refscan.py check RENDER REF` scores a render against it out of 100 and says what differs.
- **Make what is missing** (`scaffold.py`, `film.extend`, `themes.register`, callable `fx=` and `grade=`): new scenes, themes and effects for one video, recorded in `script.md`; promote them into the toolkit when reused.
- **Variety guard** (`variety.py`): every finished render records its theme, genre, grade, fx, scene mix and palette in `history.json`; a render warns when it repeats a recent video; `variety.py --suggest` lists what has not been used.
- **Local tool scan** (`toolscan.py`, run by `setup.sh`): writes `TOOLS.md` and `tools.json` listing every tool and app on the machine (Blender, Codex, Claude Code, Godot, Unreal, Unity, ffmpeg, ImageMagick, whisper, Xcode, Docker ...), MCP servers for Claude Code and Codex, installed agent skills, local AI models (Hugging Face cache, uv tools, Ollama, LM Studio, ComfyUI), API keys set (names only), the hardware, and a "pick a tool for the need" table. Read-only.
- **Asset library** (`assets.py`): characters, character sheets, sprite sheets, turntables and 3D models are kept in `~/joyboy/assets/` with a manifest, a saved recipe and older versions, listed in `INDEX.md`, and rebuilt with `assets.py rebuild NAME`. `film.asset(name)` returns a file for a script.
- **Blender, headless** (`blender_asset.py`, `blender_job.py`): `mascot` builds a recolourable toy character (idle, walk or hop) and registers its 3D model, character sheet and sprite sheet; `sheet`, `turntable` and `sprites` do the same for any `.glb .fbx .obj .stl .blend` file.
- `film.sprite(...)` plays a sprite sheet or turntable from the library, and can walk it across the frame.
- **Companion skills**: `install.sh` now also installs the 13 `/ig-*` Instagram skills from `skills/` and links the Agent Reach skill when its command is installed (`--no-companions` skips both). SKILL.md says when to hand off to each.
- **Twelve music genres** (`genre=`): lofi, house, trap, synthwave, ambient, acoustic, funk, epic, phonk, afro, pop and techno. Each has its own instruments (plucked strings, supersaw, pads, 808s, acid bass, marimba, claps, shakers, cowbell, congas and more), groove, swing, sidechain pumping and tempo range. Tempo, key, mode, chord progression, drum variant and the melody itself are written from the seed, with an intro, a mid-film breakdown and risers and fills. With no `genre`, the mood and the film's name pick one, so default videos no longer share one sound. `genre="classic"` keeps the old score.
- **Eight visual themes** (`theme=`): flat, studio, blueprint, brutal, aurora, paper, neon and retro. Each sets the background, palette, typeface, ink colour and finish, and the text colour flips between black and white to stay readable. The original dark look remains when no theme is given.
- **Twenty-one new scene types** for formats that are trending now: `kinetic`, `highlight`, `stages`, `timeline`, `countdown`, `versus`, `product`, `chat`, `satisfying`, `stick`, `anatomy`, `before_after`, `wire` (3D wireframes that draw themselves), `cta` (comment-keyword call to action), `skit` (two-character comedy dialogue with name pills on a bokeh room) and `laptop` (POV laptop shot with mirror reflection), `notes` (Apple Notes ad), `review` (social proof cards), `wrapped` (year-in-review story cards), `lyrics` (karaoke) and `changelog` (release notes), each with matching sound effects.
- `Film(grade=...)` colour grades (teal_orange, noir, bleach, sunset, mint, cross, pastel, night), `Film(mblur=True)` film-style motion blur, `film.safe` for platform safe zones, and an `.srt` caption file written beside any video with narration.
- `Film(fx="vhs")` and `fx="pixel"`: whole-film retro treatments.
- Playbook rows for the formats found on current feeds, each naming a theme, genre and scene mix.

### Changed

- Text drawn by scenes now follows the film's ink colour instead of always being white (no change without a theme).

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
