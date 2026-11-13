---
name: joyboy
description: Make any kind of video fast, entirely in code - promos, teasers, logo reveals, explainers, app demos, website tours, slideshows, data stories, reels, short films and dialogues - with generated music, ambient sound, sound effects and narration, rendered to MP4 in portrait, landscape or square. A scene-based fast path turns ten lines into a finished video; a full kit (camera moves over stills, type, logo animation, charts, maps, icons, talking characters, procedural 3D worlds, GSAP, effects, synthesized audio) covers anything custom. Python and ffmpeg at the core (node and Chrome for web, character and 3D scenes); no video model or stock footage. Use this skill whenever the user asks for a video, reel, short film, story, skit, teaser, trailer, ad, promo, explainer, slideshow, logo animation, intro/outro, motion graphics or "a video like this one", wants stills or screenshots animated, wants music, sound effects or voiceover for a video, or says "joyboy" - even if they do not say how.
---

# joyboy: a technique kit for code-rendered video

This skill is a menu of techniques, not a formula. The concept, story, order of shots, mood, pacing and words come from the user's request and the material in front of you; decide those fresh every time. Then use the tables below to pick what to build each moment with.

Every frame is computed by a Python `frame(f)` function, the audio is synthesized in NumPy, and ffmpeg assembles the MP4. That makes results exact, repeatable and easy to recut.

- `scripts/quick.py` - the fast path: describe the video as a list of scenes and get an MP4 with music and narration. Start here for almost every video.
- `scripts/maps.py` - street maps from OpenStreetMap data.
- `scripts/web_capture.mjs`, `scripts/web_template.html` - GSAP / web animation scenes.
- `scripts/model3d.py` - real 3D model files (GLB) as scenes, drawn with 67.js.
- `scripts/gss_template.html` - 3D scenes written in GSS.
- `scripts/icon.mjs`, `scripts/icon_anim_template.html` - icon search and rendering (react-icons), animated Lucide icons.
- `scripts/avatar.mjs` - illustrated people from DiceBear, still or talking.
- `scripts/sitekit.py`, `scripts/site_save.mjs` - download a real public website and animate its own elements (tours, explainers, walk-throughs).
- `scripts/world.py`, `scripts/world.js`, `scripts/world_still.mjs` - story scenes in a procedural low-poly 3D world with people, weather, time of day and camera shots.
- `scripts/ambience.py` - background sound synthesized in code (fire, wind, rain, thunder, waves, stream, crickets, traffic).
- `scripts/joyboy.py` - picture toolkit (import as `jb`, call `jb.init(w, h, fps)` first).
- `scripts/score.py` - audio toolkit (`Score` class, everything placed by frame number).
- `scripts/example_film.py` - shows how the pieces plug together and how to render. It is an API demo only; do not copy its storyline, wording or shot order.
- `references/playbooks.md` - common kinds of video and the scenes that suit each.
- `references/recipes.md` - parameter values and formulas for each technique, plus known pitfalls. Read it when you start building.

## Brief first, then decide

Before making anything, collect a short brief from the user, one simple question at a time. After the brief, stop asking and use your own judgment for everything else.

**How to ask**

- One question per message, in everyday words, with two to four ready-made choices plus room for their own answer. Use the question tool (`AskUserQuestion`) when it is available.
- Skip any question the request, the files or the conversation already answers. If the user says "you decide" or "just make it", stop asking and choose.
- Never ask technical questions (frame rate, codecs, fonts files, resolution numbers). Translate the plain answers into those choices yourself.

**The questions, in order**

1. **What is the video for?** What it is about and what viewers should do or feel after watching (know the name, visit, buy, sign up, remember).
2. **Where will it be shown?** Instagram / TikTok / Shorts (tall), YouTube / website / presentation (wide), feed post (square). This sets the shape.
3. **What do you already have?** Logo, photos, video clips, screenshots, brand colours, written text, a reference video they like. Ask where the files are.
4. **What should it say?** The name, the main message, any offer, date, place, link or contact. Offer to write the words if they have none.
5. **Which language?** For the on-screen words and the voice-over (they can differ). Default to the language the user is writing in.
6. **What style?** Cinematic and dramatic, upbeat and energetic, calm and gentle, clean and techy. Offer to match their reference or brand. The answer sets the mood; the look, music variation and sounds are then chosen to fit the subject (see "Look and sound").
7. **How long?** About 10 seconds, 20-30 seconds, about a minute.
8. **What sound?** Music only, music with a spoken voiceover, their own song, no sound.
9. **How should it open and close?** What the intro shows (logo, name, a hook line) and what the outro leaves people with (call to action, contact, date, "coming soon").
10. **Anything to avoid?** Old names or logos, colours, words, images that must not appear.

**Then**

- Repeat the brief back in three or four plain lines ("Here's what I'll make: ...") and start. Do not wait for approval unless something in the brief is contradictory.
- From here on, do not ask again. Make every remaining creative and technical choice yourself, finish the video, and mention the notable choices in a line or two when delivering so they can ask for a change.
- The only later questions allowed: when you truly cannot continue, or before something risky and hard to undo (deleting their files, installing system software, spending money, publishing). One short, simple question.
- When the user asks for a change to an existing video, do not re-run the brief. Make the change.

## Intro and outro: always

Every video opens with a proper intro and closes with a proper outro, whatever its length or kind. They are what make it feel finished and tell viewers whose it is.

- **Intro (first 2-4 seconds):** establishes what this is - the name or a hook line, an optional short line under it, and the logo when there is one. Use `film.intro(title, sub, logo)`, or a `title`, `crt` or `logo` scene when the concept calls for a different opening.
- **Outro (last 3-5 seconds):** leaves viewers with the next step - the logo, the closing words (call to action, date, link, contact, "coming soon"), then a fade out. Use `film.outro(text, sub, logo)`, or an `end` or `logo` scene.
- Give both the same look (logo, colours, typeface) so the video is bookended.
- For a teaser that must not show the name, the intro is a hook and the outro carries the mark and closing words only.
- `quick.py` refuses to render a film whose first scene is not an intro or whose last is not an outro. In a fully custom film, build both yourself.
- The music should begin with the intro and resolve under the outro; the generated score does this.

## Work in parallel

Speed matters. Whenever two things do not depend on each other, do them at the same time instead of one after the other.

**Parallel tool calls.** Send independent calls together in one message, not as a chain of single steps:

- reading the artwork, the logo, the reference frames and the brand's text files;
- running setup and inspecting the user's files;
- searching for several icons, geocoding several places, generating several narration lines;
- rendering contact sheets for portrait and landscape, or for different parts of the video;
- final renders of different shapes or versions: each is its own command, but run them one after another, not together (see "Go easy on the machine").

**Parallel subagents.** When subagents are available, hand each self-contained piece to one and keep working on the rest. This skill is the user's standing instruction to do so, so do not ask first. Good pieces to hand off:

- gathering and preparing assets (finding and cropping images, extracting frames from a reference video, saving brand fonts and colours);
- reading the brand's website or documents and returning the usable lines and facts;
- writing each GSAP/web scene page (one subagent per page) from a clear description;
- writing the narration script, or translating on-screen text and narration into another language;
- building one long section of a custom film (one subagent per act) against agreed frame numbers and helper names;
- checking finished contact sheets for overflow, overlap and unreadable text, one shape per subagent;
- producing the other shapes (landscape, square) once the first is approved, one render at a time.

Give each subagent what it needs to work alone: the workspace path, the project folder, the brief, the palette and fonts, the exact file to write, and what "done" looks like. Tell it to read `SYSTEM.md` and not to install anything. Do not hand off work that is one small step, or two pieces that edit the same file.

**Already parallel.** `film.render()` splits the frames across the fast CPU cores by itself (leaving one free), and narration, clips, icons, maps and web captures are cached, so a second run only redoes what changed.

**What stays in order.** The brief comes first. The frame plan (scene list and timings) must exist before pieces are built against it. The final check of the finished MP4 comes last.

## Go easy on the machine: fast, but never overheating

Making video is heavy work, and this runs on the user's own computer, often a laptop. Speed matters, but the machine's health comes first: work as fast as the machine can go while it stays cool and usable, and no faster. This never means lowering quality; the picture, sound and resolution delivered are the same. Only the pacing changes.

**Built in (do not switch these off to save time):**

- A render uses the fast processor cores minus one, at low priority, with a small encoder thread count, so the computer stays responsive for the user.
- While rendering, the heat is checked every few seconds. If the system reports it is slowing the processor to cool down, the render waits until it recovers and then carries on; it prints how long it paused. `JOYBOY_JOBS=<n>` and `JOYBOY_COOL=0` exist for unusual machines only; never set them just to go faster.

**How to work:**

- **One heavy job at a time.** A full render, a web or world capture, and a package install are each heavy. Run them one after another, never side by side. Light work (reading files, searching icons, geocoding, writing scene pages, checking sheets) can still run in parallel with anything.
- **Check before a long job.** If the previous job just finished and the machine was working hard, or the user says the fans are loud or the laptop is hot, look at the heat first (`pmset -g therm` on a Mac; `python -c "import joyboy as jb; print(jb.heat())"` anywhere). If it says hot, wait a minute and check again before starting.
- **Do the cheap thing first.** Stills and contact sheets before a draft, a draft (`JOYBOY_DRAFT=1`) before the full render, and the full render once. Do not re-render the whole video to change one word when a cached scene can be reused.
- **Do not repeat work.** Captures, voices, icons, maps and characters are cached; keep their inputs unchanged between runs so the caches are used. Change one shot at a time.
- **Pick the lighter tool when the result is the same.** A built-in scene instead of a web capture, a 2D `talk` scene instead of a world when the story does not need a place.
- **Long videos:** over about two minutes, or many world shots, render in parts across a few runs with a short rest between, and say so.
- **Leave it clean.** No stray browsers, servers or background processes left running when the job ends.
- **Tell the user** if the machine had to pause to cool, if a job will take more than a few minutes, or if it is running on battery and the job is long (suggest plugging in).
- **Never** disable system protections, change fan or power settings, or keep the machine awake by force to finish faster.

## Workspace: one folder, set up once

All joyboy work lives in one persistent folder so that tools are installed once and reused for every video, instead of being set up again each time.

- **Location:** `~/joyboy` by default. If the user names a different folder, use that and keep using it; if `JOYBOY_HOME` is set, that is the folder.
- **Start of every video:** run `bash <this skill>/scripts/setup.sh [folder]`, then read `SYSTEM.md` in the workspace (see below). It is safe to run every time: it creates the folder, a Python environment and the toolkit copy only if they are missing, installs only packages that are not already there, and prints `READY` with the paths. When everything exists it does nothing and returns at once.
- **Do not install anything else by default.** A new video uses what is already in the workspace. Add a package or tool only when that particular video needs something the kit does not have (for example an SVG rasterizer or a new font), install it into the same workspace environment so the next video can reuse it, and tell the user what was added and why.
- **Layout:**

```
~/joyboy/
├── .venv/                 Python environment (created once)
├── SYSTEM.md              checklist of what this machine has (read first)
├── voices/                Piper voice models (downloaded once)
├── fonts/                 brand fonts saved for reuse
├── web/                   GSAP + capture script + page template (installed once)
├── maps/                  cached OpenStreetMap data
├── icons/                 rendered icons, cached
├── avatars/               DiceBear characters, cached
├── brand/<brand>/         shared brand kit: brand.md, logo, palette, facts
├── captures/              cached web-page screenshots
├── lib/                   joyboy.py, score.py, quick.py (copied from the skill, refreshed when it changes)
└── projects/
    └── <video-name>/      one folder per video
        ├── script.md      the script, rewritten on every render (see "Keep every video and its script together")
        ├── film.py        the code that makes the video
        ├── assets/        artwork, logos, clips copied in for this video
        ├── work/          contact sheets, test renders, caches
        └── out/           finished MP4s only
```

- **Each video gets its own folder** under `projects/`, named after the video (lowercase, hyphens). Versions and other aspect ratios of the same video go in the same folder. Never write generated files into the user's code repository or other folders unless they ask for a copy there.
- **Running:** use the workspace Python, `~/joyboy/.venv/bin/python film.py ...`, and import the toolkit from the workspace: `sys.path.insert(0, os.path.expanduser("~/joyboy/lib"))`.
- **Delivering:** the finished file stays in `projects/<video-name>/out/`. Hand it over from there as described in "The final message", and copy it elsewhere only if they ask.

## Keep every video and its script together, in order

This is a core habit of this skill, not housekeeping to skip. Anyone opening the workspace months later should find any video, see exactly what is in it, and be able to change it, without reading code.

**One folder per video, always the same shape:**

```
~/joyboy/projects/<video-name>/
├── script.md      the script: shot list with times, on-screen words, narration, files used, and notes
├── film.py        the code that makes the video
├── assets/        everything supplied or prepared for this video (logo, images, clips, pages, narration files)
├── work/          previews, contact sheets and caches (safe to delete)
└── out/           finished videos only
```

- **The script always exists and always matches the video.** `film.render()` rewrites `script.md` on every render from the scenes themselves, so it cannot drift. For a fully custom film that does not use `quick.py`, write and update `script.md` by hand in the same layout.
- **Write the thinking into `## Notes` in `script.md`** as soon as the brief is done: the brief's answers, the concept in two or three lines, and later every decision or change the user asked for, with the date. This section is kept between renders. It is what lets a later session pick the video up.
- **Name things so they sort and explain themselves.** Folder: lowercase words with hyphens, saying what the video is (`spring-sale-teaser`, not `video2` or `final`). Outputs: `<video-name>.mp4`, with the shape or version added when there is more than one (`<video-name>-landscape.mp4`, `<video-name>-v2.mp4`). Never `final`, `new`, `test` or `copy`.
- **Versions:** when the user asks for a change, render over the current file unless they want to keep the old one; if they do, keep it as `-v1` and note in `script.md` what changed in `-v2`. Other shapes and languages of the same video live in the same folder and the same `script.md` notes.
- **Assets live inside the project.** Copy supplied files into `assets/` instead of pointing at Downloads or the desktop, so the project still renders later. Shared brand material (logo, fonts, palette, facts) goes in `~/joyboy/brand/<brand>/` with a short `brand.md`, and is reused by every video for that brand.
- **`out/` holds finished videos only.** Drafts, sheets and intermediate files go in `work/`. Delete failed or abandoned attempts instead of leaving them beside the real ones.
- **Leave the workspace tidy at the end of every job:** no stray folders in `projects/`, no test scratch left behind, `script.md` present and current, and `setup.sh` run once more so `SYSTEM.md` lists the project and its videos.
- **When delivering,** follow "The final message": the video first, then where it and its script are.

## The final message: the video first, then a few plain lines

The last thing the user sees decides how the whole job feels. They asked for a video, so hand them the video, in the easiest way their screen allows, and say only what they need to act on. A finished render prints a `READY TO DELIVER` block with the exact path, the facts line, a preview strip and the script path; build the message from it instead of from memory.

**1. Show the video, do not describe it.** Use the best way available, in this order:

1. **A file-sending tool is available** (for example `SendUserFile` or `present_files`): send the MP4 with it, set to display or play in place, with a caption of a few words. This is the best experience: the user presses play right in the conversation.
2. **Files can be linked** (the video is inside a folder the app can open): put a link to the MP4 on its own line.
3. **Neither** (a plain terminal): put the full path on its own line, and under it a one-line command that opens it, in its own code block: `open "<path>"` on a Mac, `xdg-open` on Linux, `start ""` on Windows.

Never make the user hunt for the file, and never paste a long folder tree. When the video cannot play in place, also send or link the preview strip (`work/<name>-preview.jpg`), so they can see at a glance what was made.

**2. Then at most five short lines, in this order.** No headings, no tables, no bullet nests.

1. **What it is:** the name in bold, then "is ready", then the facts line in everyday words: length, shape, sound. Say "tall", "wide" or "square", and what that shape suits (Reels and Shorts, YouTube, a feed post), not pixel counts.
2. **Where it is:** the path to the video, and that its script is beside it.
3. **What I chose:** the two or three choices they would most want to know (the idea, the mood, the voice), in one line.
4. **Not checked:** one honest line. You cannot watch motion or hear sound; add anything specific that worries you (a name's pronunciation, small text). Leave nothing important unsaid, and add nothing that is not.
5. **Want a change?** Invite it with two or three examples that fit this video, in their words ("make it shorter", "calmer music", "a wide version for YouTube", "change the last line"). This replaces any question.

**Example**

> *(the video, playing in place)*
>
> **Spring sale teaser** is ready: 24 seconds, tall for Reels and Shorts, with music and a voice-over.
> It's saved at `~/joyboy/projects/spring-sale-teaser/out/spring-sale-teaser.mp4`, with its script in the same folder.
> I went with a fast, upbeat cut, your orange and navy, and a warm female voice.
> I can't watch or listen to it myself, so please check how the voice says "Kozhikode".
> Want a change? Just say it: "make it shorter", "calmer music", or "a wide version for YouTube".

**Keep out of the final message:**

- the story of how it was made, the scene list, tool names, file formats, frame rates, bitrates, or anything else they did not ask about (the scene list lives in `script.md`);
- more than one question, and usually none: if something was unclear, say what you chose;
- apologies, praise for the result, and filler openings or closings;
- file size, unless it is over about 50 MB, in which case say so and offer a smaller copy.

**Variations**

- **Several videos or shapes:** send each file, then one line per video (name, length, shape), and the where, chose, not-checked and change lines once for the set.
- **A change to an existing video:** send the new video and say in one line what changed. Skip the rest unless it is different from last time.
- **It could not be finished:** say that first, plainly, with what is done and what is needed from them. Do not send a broken video as if it were finished.
- **While working:** keep updates to one short line each ("Draft looks right, rendering the full version now").
- Write it in the language the user is writing in.

## Installing things: bun first, reuse what is there

Nothing is downloaded twice. Before installing anything, check `SYSTEM.md` and the workspace; use what is already there.

- **JavaScript packages go in with bun** when the machine has it (`bun add <package>` inside `~/joyboy/web`). Bun is several times faster than npm, and it keeps one shared cache for the whole machine, so a package already downloaded for any other project is linked in instead of fetched again. `setup.sh` does this by itself.
- **No bun: carry on with npm, and suggest bun once.** `setup.sh` falls back to npm (reusing npm's own cache). The first time this happens, tell the user in two plain lines, then continue without waiting:
  - what they gain: installs that take seconds instead of minutes, and no re-downloading of packages their other projects already have;
  - how: `curl -fsSL https://bun.sh/install | bash` (or `brew install bun`), which they run themselves.
  Do not install bun for them, and do not bring it up again once they have seen the suggestion (note it in `SYSTEM.md` under Notes).
- **Python packages** reuse the system's: the workspace environment is created with access to packages already installed, and `setup.sh` installs only the ones that are missing.
- **Voices, icons, maps, page captures and web scenes** are cached in the workspace and reused by every later video.
- A video that needs something new gets it installed once into the workspace, with one line to the user saying what and why.

## System checklist: read `SYSTEM.md` first

`~/joyboy/SYSTEM.md` is a short checklist of what this machine already has: Python and packages, ffmpeg, voice-over engines and voices, fonts, toolkit files, and existing projects. `setup.sh` rewrites it on every run.

- Read it right after running setup and before planning the video. It tells you what is ready, so you never check or install something twice.
- Plan with what is ticked. If a video needs something that is not ticked, install it into the workspace once, run `setup.sh` again so the checklist updates, and tell the user what was added.
- The `## Notes` section at the bottom is kept between runs. Write there anything worth remembering that setup cannot detect: things installed by hand, the user's preferred voice, brand fonts saved to `fonts/`, standing preferences. Never write passwords or API keys in it.

## Voice-over: which voice to use

Use the best voice available, in this order. `quick.py` does this automatically for `voice="..."`.

1. **ElevenLabs** - when an ElevenLabs tool (MCP) is available in the session, or `ELEVENLABS_API_KEY` is set. With an MCP tool, generate the audio file with it, save it in the project's `assets/`, and pass the file path as `voice="assets/line1.mp3"`. With the key set, `quick.py` calls the API itself.
2. **Piper TTS** - the default when ElevenLabs is not available. It runs on this machine, is free, and is already installed in the workspace with voices in `~/joyboy/voices/`. Pick a voice with `Film(..., voice="ryan")` (any part of the voice file name); more voices can be downloaded once with `~/joyboy/.venv/bin/python -m piper.download_voices --download-dir ~/joyboy/voices <name>`.
3. **System voice (`say`)** - last resort only, if Piper is missing or fails.

**The voice speaks the language the person wants.** Pass it once: `Film(..., lang="es")` (two-letter code: `en`, `es`, `fr`, `de`, `ar`, `hi`, ...).

- Piper uses a voice for that language. If none is installed yet, one is downloaded once into `~/joyboy/voices/` and reused from then on (about 180 voices across some 40 languages exist; list them with `python -m piper.download_voices`).
- Write the narration text in that language, in its own script. Never feed text in one language to a voice of another; it will be mispronounced.
- Indian languages with Piper voices include Malayalam (`ml_IN-arjun-medium`, `ml_IN-meera-medium`), Hindi and Telugu; download both voices of a language when two people talk, and give each person one with `voice="arjun"` / `voice="meera"`.
- If Piper has no voice for the language, the system voice for that language is used; if there is none either, say so plainly and offer ElevenLabs or on-screen text only.
- ElevenLabs handles the language from the text itself.
- On-screen text in scripts that need shaping (Arabic, Hindi, Malayalam and other Indic scripts) does not render correctly through the built-in text drawing on this setup. For those, put the text in a `web` scene, where the browser shapes it properly, with a font that covers the script. World shots already do this for their captions and titles (see "Worlds").

**Emotional voices: Supertonic (optional).** Piper reads clearly but flatly. When the piece needs feeling in the voice (a story, a dialogue, characters in a world, a heartfelt message, comedy), use Supertonic for those voices. It runs on the user's machine, is fast, and has ten voices: `F1` to `F5` and `M1` to `M5`.

- **Choose it by voice name.** Give a character one of its voices, `film.person("meera", ..., voice="F2")`, and that character speaks with Supertonic while others can stay on Piper. For narration, `Film(..., tts="supertonic", voice_name="M1")`.
- **Mark the feeling in the line** with expression tags: `<laugh>`, `<sigh>`, `<breath>`. Put a tag where the sound should happen: `"Every evening. <laugh> Somebody had to keep your seat warm."` Use them sparingly, at most one in a line and not on every line, and only where a person would really laugh, sigh or catch their breath.
- **Captions stay clean.** Tags are removed from captions by themselves, and any other engine skips them, so a tagged line is safe whichever voice ends up speaking it.
- **Give each character a different voice**, and keep one voice per character for the whole film. Try two or three voices on one line and keep the one that suits the character's age and mood.
- **Install it once, only when a video needs it:** `~/joyboy/.venv/bin/python -m pip install supertonic`. Its model (about 400 MB) downloads on first use into `~/joyboy/voices/supertonic` and is reused. `SYSTEM.md` shows whether it is ready. Tell the user in one line when it is installed.
- **Languages:** English, Hindi, Arabic and 28 others (not Malayalam and not most other Indian languages). For a language it lacks, the line falls back to Piper by itself; say so, because the feeling will be flatter.
- **Licence:** the Supertonic model is under the OpenRAIL-M licence, which sets conditions on use. Mention it once when a user's video is for commercial use, and never copy the model into a project or a repository.
- `Film(tts="piper" | "elevenlabs" | "say" | "supertonic")` puts one engine first for the whole film; without it the order above applies, with Supertonic used only for its own voice names.

**Set the speaking speed from the script.** Narration speed is a setting, not a fixed default: `Film(..., pace=1.0)` for the whole video and `pace=` on any scene to override it. `1.0` is the voice's normal speed; lower is slower, higher is faster. It works with Piper (phoneme length and the pause between sentences), ElevenLabs and the system voice.

| Script | Pace |
|---|---|
| Calm, emotional, reflective, luxury, memorial | 0.85-0.92 |
| Explainer, tutorial, documentary, anything with numbers or steps to follow | 0.95-1.0 |
| Brand story, product overview, general narration | 1.0 |
| Promo, offer, social reel, upbeat announcement | 1.08-1.15 |
| Urgent call to action, disclaimer, fast list | 1.15-1.25 |

- Choose the pace by reading the script, and vary it inside one video where the script changes mood: a slower opening line, a brisker middle, a slower closing line that lands.
- Slow down for lines with names, prices, dates, addresses or anything the listener must catch; speed up only for lines that are easy to follow.
- `pace="fit"` keeps a scene at its set length and speaks as fast as needed to fit, up to 1.3. Use it when the picture's timing is fixed (a clip, a web scene, a beat-locked cut). If the line still does not fit at 1.3, the scene stretches; shorten the line instead of pushing the voice faster.
- Stay between about 0.8 and 1.3. Outside that range the voice stops sounding natural.
- Match the mood: a slow voice over a fast cut, or the reverse, feels wrong. Pace, music mood and cutting speed should agree.

Do not ask the user which engine to use; check `SYSTEM.md` and follow the order. Tell them in one line which voice was used. Text sent to ElevenLabs leaves the machine; Piper and the system voice stay local.

## Fast path: build any video from scenes

For speed, write the video as a short list of scenes with `quick.py`. A 30-second video is about ten lines and renders as a draft in seconds. Scene lengths snap to the music's beat, transitions and sound accents are added automatically, and the same script renders in any shape.

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/joyboy/lib"))
from quick import Film

film = Film("spring-sale", size="portrait", mood="upbeat", palette=["#101018", "#ff5a36", "#ffd166"])
film.intro("SPRING SALE", sub="this weekend only", logo="assets/logo.png")
film.image("assets/shop.jpg", text="Everything in store", move="push")
film.stat("40%", "off all shoes")
film.outro("OPEN 9 TO 9", sub="12 Market Street", logo="assets/logo.png")
film.render()
```

| Scene | Use it for |
|---|---|
| `intro(title, sub, logo)` | the opening card: name or hook, short line, logo. Required first |
| `outro(text, sub, logo)` | the closing card: logo, closing words, fade out. Required last |
| `title(text, sub)` | headlines, chapter cards, hooks |
| `image(path, text, move)` | photos and artwork with a camera move (`push`, `pull`, `pan`, `pan_left`, `tilt_up`, `tilt_down`, `snap`, `parallax`, `still`) and optional caption |
| `clip(path, start, dur, text)` | a piece of existing video footage, cropped to fill |
| `words([...], per)` | kinetic type, one word per beat on colour fields |
| `bullets(title, items)` | steps, features, agendas, explainers |
| `stat(value, label)` | a single number that counts up (`"40%"`, `"$1.2M"`, `"3x"`); for a range like "3-6 weeks" use `title` |
| `bars({label: value}, title)` | horizontal bar chart |
| `columns({label: value}, title)` | vertical bar chart |
| `line(series, title, labels)` | line chart that draws itself; one or several series |
| `donut({label: value}, title, center)` | share-of-total chart with legend |
| `heatmap(grid, xlabels, ylabels, title)` | heat map from a table of numbers (activity by day and hour, etc.) |
| `icons([(icon, label, small line)], title)` | a grid of library icons with labels (features, services, benefits) |
| `film.world(...)` then `w.shot(cam, say=(person, line))` | story mode: a 3D low-poly place (forest, street, beach ...) with time of day, weather, props and talking people, filmed from different camera angles (see "Worlds") |
| `talk(person, line, role, prop)` | an illustrated character speaks a line with lip sync: dialogues, testimonials-style explainers, presenters (see "People") |
| `map(place, radius_km, pins, route, title)` | a real street map from OpenStreetMap data with dropping pins and a route line |
| `model(glb)` then `m.shot(cam)` | a real 3D model file shown with camera moves (see "3D models") |
| `web(html, dur, clock)` | a GSAP / web animation, or a GSS 3D scene with `clock="virtual"`, captured frame by frame |
| `quote(text, by)` | testimonials, quotations, lyrics, poems |
| `phone(screenshot, text, status)` | app and website demos inside the standard titanium phone frame (tall screenshots scroll) |
| `browser(screenshot, url, text)` | a desktop browser window with a page scrolling inside (website tours) |
| `crt([lines])` | retro terminal that types, then blooms to white |
| `lockcut(images, per)` | fast-cut reel where the logo painted in every image stays locked in one spot while the pictures flash past |
| `window(mark, images)` | the logo as a window: outline lands, images play through its shape, it blows open to the full picture, the logo springs back |
| `slices(images, count)` | vertical strips from different images slide in from top and bottom and march sideways on the beat |
| `carousel(items)` | cards (images, or icon names drawn as app-icon tiles) snap past with motion blur; the last one opens to fill the frame |
| `grid(mark)` | a wall of small logos with colour ripples from the centre, zoom and tilt punches on the beat |
| `tunnel(mark)` | nested logo shapes in the palette colours rushing outward, twisting and stepping on the beat |
| `loader(label, done, mark)` | glitchy loading screen: progress bar and percentage, equaliser bars, scan lines, colour split, then a typed closing word |
| `logo(mark, text, sub, style)` | logo reveal from a logo image: `trace` (line of light, then hit) or `pop` |
| `end(text, sub)` | closing card, call to action, contact line |
| `custom(fn, dur)` | anything else: `fn(u, n, f)` returns a frame built with the `jb` helpers below |

Options every scene accepts:

- `dur` - seconds. `tr` - transition into the scene: `cut`, `fade`, `whip`, `white`, `zoom`, `wipe` (diagonal), `iris`, `bars`, `doors`, `pie`, `glitch`.
- `pace` - narration speed for the scene (`1.0` normal, `0.9` slower, `1.15` brisker, `"fit"` to fit the scene's length); see "Voice-over".
- `voice="..."` - narration: the words to speak, or a path to a ready audio file. Spoken by ElevenLabs, Piper or the system voice in that order (see "Voice-over"); the scene stretches to fit and the music ducks under it.
- `bg` - a colour (`"#112233"`), a two-colour gradient (`("#0b0b10", "#2a1f8f")`), or an image path.
- `note="sample data"` - a small footnote pill at the bottom of the scene (disclaimers, "example", sources). Put it on every scene that needs it.
- `voice_at=1.0` - seconds into the scene that the narration starts (default 0.2), to line a spoken line up with what appears.
- `image(..., at="top")` puts the caption at the top when the subject sits low in the picture. `title`, `intro` and `outro` take `y=0.3` (fraction of the frame height) to move their text off a busy part of a background picture.

Film options:

- `size`: `portrait`, `landscape`, `square`, `4:5`, or `(w, h)`.
- `mood`: `cinematic`, `upbeat`, `calm`, `tech`, `hype` (180 BPM, hard cuts, for fast reels), `none` (sets tempo, default transition and the generated music).
- `lang` - language of the voice-over, e.g. `"es"`; `pace` - default narration speed (see "Voice-over").
- `look` - the finish on the picture: `cinematic`, `soft`, `clean`, `punchy`, `warm`, `cool`, `vintage`, `none`, or a dict of strengths (see "Look and sound"). Choose it for every video.
- `music_seed`, `key`, `energy`, `air` - which variation of the generated music, its key, how full it is, and a wind bed; `sfx`, `mute` - level of the automatic sounds and which to leave out.
- `bloom` - the glow on bright areas (default 0.8, or what the look sets). Use `bloom=0.2` or less for light or cream backgrounds, which otherwise wash out.
- `tts` - the voice engine to prefer (`"supertonic"` for emotional voices; see "Voice-over").
- `palette`, `font`, `font_bold`, `bpm`, `voice_name` (a Piper voice name such as `"ryan"`, or an ElevenLabs voice id).
- `film.music("song.mp3")` uses an existing track instead of generated music.

Real web pages: `shot = film.capture(url, "mobile" | "desktop")` takes a full-length screenshot of a public page (cached in `~/joyboy/captures/`). Use it with `phone(shot, ...)` or `browser(shot, url=...)`. Long pages scroll top to bottom by default; pass `span=(0.0, 0.3)` to scroll only part of the page (start and end as fractions of its length), so a long capture does not race by. Capture the user's real site for a website tour instead of mocking it up; never capture pages behind a login.

Working fast:

- Iterate in draft: `JOYBOY_DRAFT=1 python film.py` renders at half size, several times faster, into `work/<name>-draft.mp4`. Render full quality once, at the end, into `out/`.
- `python film.py plan` prints every scene with its start frame; pick sheet frames from it, then check with `python film.py sheet work/s.jpg <frames...>`.
- Make another shape by changing `size` only. Re-check text placement on a sheet.
- Create files a script needs (generated images, logos) only if they do not exist yet, because the script runs several times in parallel during a render.
- Mix freely: use scenes for most of the video and `custom` for the one or two shots that need something special. Helpers for custom scenes: `film.mark(path)` (logo outline for `jb.dmask` / `jb.trace`), `film.head(img, title, u)` (fitted heading), `film.text_width(text, size, bold)`, `film.block`, `film.ltext`, `film.put_icon` (call `film.icons_ready([names])` once first), `film.card` (rounded panel), `film.bg`.

`references/playbooks.md` lists common kinds of video and which scenes suit them. Use it for speed when the request is ordinary; ignore it when the concept calls for something else.

## Working with someone's website: download it, then use its parts

When the user points at a website that is not part of the project in front of you ("make an explainer of example.com", "tour this page", "animate their pricing section", "show how to sign up on this site") do not rebuild the page by hand and do not settle for one flat screenshot. Download the page once and work with its real elements.

```python
s = film.site("https://example.com")            # downloads once, cached in ~/joyboy/captures/sites/ ("mobile" for the phone layout)
s.show()                                        # lists every element: id, kind, position, words
s.overview("work/site.jpg")                     # the page with every element numbered - look at it before choosing
s.shot(dur=3, text="The home page")             # the top of the page
s.shot(focus="Pricing", label="Three plans", voice="Pick the plan that fits.")
s.shot(focus=12, lift=True, click=True, zoom=1.3)
s.shot(scroll=(0.2, 0.7), dur=4)                # a plain scroll
```

- **What gets saved:** the whole page as a sharp image, the page itself (`page.mhtml`), and `elements.json` with each heading, text, button, link, image, card, section and input: its words, selector and position. `s.meta` also has the page's title, colours and fonts; use them for the intro, outro and labels so the video matches the site.
- **What a shot can do:** travel to an element (`focus=` its id or words it contains), light it while the rest dims, `label=` it, `lift=` it off the page, `click=` it with a cursor, go closer with `zoom=`, or `scroll=` plainly. Each shot is one scene, takes `voice`, `text`, `tr` and `note` like any scene, and carries on from where the last one ended, so the camera travels over the page. Sounds (move, label, click) are added to match.
- **Always run `s.show()` and look at the overview first**, then pick elements by id; do not guess what is on the page.
- **Going further:** the element positions are yours to use in a `custom` scene (cut an element out of `page.png` and fly it, stack cards, build a chart from the page's numbers), and a second page of the site is just another `film.site(url)`. For the page inside a phone or browser window, keep using `film.capture` with `phone()` / `browser()`.
- **Only public pages.** Nothing is typed, clicked or submitted on the real site; pages behind a login are not for this. It is someone else's site: show it honestly, do not alter its words or pass it off as the user's, and leave people's names and faces on it out of focus shots unless the user asks.

## Look and sound: choose them for each video

No two videos should look or sound the same by accident. The finish on the picture, the music and the automatic sounds are choices made from the brief, like the words and the shots. Decide them on purpose for every video and say in a line what was chosen.

**Look** (`Film(..., look="...")`): how the finished picture is treated.

| Look | What it does | Suits |
|---|---|---|
| `cinematic` | dark corners, glow, lens streak, colour fringing, tinted shadows, grain | trailers, drama, launches |
| `soft` | a gentle version of the same, slightly warm | stories, calm brands, explainers |
| `clean` | true colours, no dark corners, no grain | apps, products, data, screenshots, anything with a UI or a light background |
| `punchy` | strong contrast and colour, little vignette | reels, offers, sport, energetic promos |
| `warm` | golden tone | food, home, festivals, nostalgia |
| `cool` | blue tone | tech, night, rain, winter |
| `vintage` | faded colour, heavy grain and corners | memories, retro |
| `none` | the picture exactly as drawn | when the artwork already has its own finish, or colours must match a brand exactly |

- With no `look`, the mood picks one (cinematic: `cinematic`, calm: `soft`, upbeat and hype: `punchy`, tech and none: `clean`). Do not rely on that; choose the look from the subject. A food brand in a calm video wants `warm`; an app demo wants `clean` whatever the mood.
- Fine control: pass a dict, optionally starting from a look, with any of `vignette`, `tint`, `fringe`, `contrast`, `streak`, `warmth` (-1 cool to +1 warm), `sat`, `grain`, `glow` (the soft centre glow on plain colour backgrounds), each a strength where 0 is off and 1 is the classic amount: `look={"base": "warm", "vignette": 0, "grain": 0.02}`. `bloom=` is still its own Film option.
- A vignette darkens screenshots, logos near the edge and light backgrounds; turn it off for those. Brand colours shift under `warm`, `cool`, `vintage` and `cinematic`; use `clean` or `none` when they must be exact.
- Worlds and web scenes get the same finish as everything else, so the look applies to the whole film.

**Music** is generated per video, not per mood.

- Each film gets its own variation from a seed made from the film's name: one of three chord sets, a starting point in the loop, a key, and one of three arrangements per mood (for calm: electric piano with bells, piano arpeggio over strings, or a music-box melody over a choir). The same film always gets the same music.
- `music_seed=<number>` picks another variation; try two or three and keep the one whose printed levels and character fit. `key=<semitones>` moves it up or down, `energy=` (about 0.5 to 1.4) makes it lighter or fuller, `bpm=` changes the tempo, `air=True` adds a soft wind bed under calm music.
- Match the music to the piece: mood first, then variation. If a series of videos should share one tune, give them the same `music_seed`; otherwise let them differ.
- `film.music("song.mp3")` uses the user's own track, and `mood="none"` gives no music.

**Automatic sounds** (the thud on a title, the whoosh on a phone, ticks on letters, hits on cuts).

- `sfx=` sets their level for the film (1 is normal, 0.5 softer, 0 none). `mute=("tick", "thud")` leaves particular ones out; names are those in "Sound that matches the picture", plus `hit` for the drum or cymbal on cuts and `whoosh` for transition whooshes.
- Use fewer of them for calm, emotional or spoken pieces, where a tick on every letter is noise; keep them for motion-graphics pieces where they make the picture feel alive.
- Do not let every video open with the same thud: vary the opening (a `logo` trace, a world shot, a `crt`) or mute it.

**Before delivering,** ask of the video: would it look and sound the same if the subject were different? If yes, change the look, the music variation or the sounds until it belongs to this subject.

## Fit: everything sized to its container

Nothing may spill out of the frame or out of the box it belongs to. The method is the one a one-page document template uses to keep any amount of typed text on a single page: lay content out at its designed size, then reduce one size factor a small step at a time until it fits the container, and scale the whole thing to the space available.

- The built-in scenes do this already. Titles, sub-lines, captions, quotes, bullet lists, chart titles and labels, legends, pin labels, terminal lines and letter-by-letter text all measure themselves against their container and step down (re-wrapping long lines first) until they fit. Pass the text as it is; do not shorten or hand-tune sizes to make it fit.
- In `custom` scenes use the same helpers so the rule still holds: `film.block(img, lines, cy, size, maxw=..., maxh=...)` for a block in a box, `film.ltext(..., maxw=...)` for a label, `film.L(text, size, track, cy)` for letter reveals, `film.wrap(text, size, bold, maxw)` to break lines. Give every piece of text a container (`maxw`, `maxh`), never a bare size.
- Images and screenshots are scaled to cover or to fit their frame, never stretched.
- Fitting has a floor: text will not shrink below a readable size. If a sheet shows text that looks too small, the content is too long for one scene, so split it into two scenes instead of forcing it.
- Always check a contact sheet in every shape being delivered; fitting is per shape.

## Phones and device frames

Whenever a phone appears, use the built-in device from `film.phone(...)`: a titanium phone frame (414 x 868 design, 70 px corner radius, brushed-metal gradient, black inner bezel, side keys, dynamic island), redrawn in code at any size.

- `film.phone(screenshot, text, status=False)`: tall screenshots scroll inside the screen, short ones are scaled to cover it. `status=True` adds a clock and battery when the screenshot has no status bar of its own. Leave it off for screenshots that already show a status bar, and for scrolling pages, where it would sit over moving content.
- For a phone inside a `custom` scene, get the parts with `film._device(height_px)` (body, mask, screen rectangle, screen mask, island mask) and composite your own moving content into the screen.
- Do not draw a different phone shape or use a stock mock-up image; keeping one device keeps every video consistent.

## Sound that matches the picture

Every scene carries sounds for what it shows, added automatically on top of the music and timed to the same frames as the animation:

| On screen | Sound |
|---|---|
| Typing (terminal) | a key click per character |
| Counter (`stat`) | ticks that slow as the number settles, then a soft ring |
| Bars and columns growing | a rising tone per bar, a pop when the last one lands |
| Line being drawn | a pencil-like scribble for as long as it draws, a pop at the end |
| Donut sweeping round | a sweep, then a pop |
| Heat map cells lighting | blips rising in pitch across the wave |
| Map route and pins | a scribble while the route draws, a pop as each pin lands |
| Bullet points arriving | a pop each |
| Titles and big words landing | a thud |
| Phone sliding in | a whoosh |
| Logo traced by light | a shimmer during the trace, then the hit |
| Letters arriving (closing words) | a light tick per letter |
| A person starting to speak (`talk`) | a soft pop as their card arrives |
| A world (`film.world`) | the place's own ambience, continuous under every shot: fire, wind, rain, thunder, waves, traffic, passing cars |

- For anything the built-in scenes cannot know about (a `custom`, `web`, `image` or `clip` scene), add cues by hand: `sfx=[(seconds, "pop"), (seconds, "scribble", duration), ...]`. Available sounds: `thud`, `pop`, `tick`, `ding`, `blip`, `rise`, `scribble`, `sweep`, `shimmer`, `whoosh`, `click`.
- The rule for custom work: if something visibly happens (appears, lands, is drawn, counts, types, slides), it gets a sound at that exact frame. Silence under visible action feels unfinished.
- Keep effects under the music and well under any narration; the mixer already lowers music and effects while a voice is speaking.

## Icons: use an icon library, never hand-drawn

Do not write SVG icons by hand or draw icon shapes with code; they come out crude and inconsistent. Take every icon from an icon library that is already installed in the workspace.

**Still icons: react-icons.** About 30 sets in one package: Lucide (`Lu`), Tabler (`Tb`), Material (`Md`), Font Awesome (`Fa`), Heroicons (`Hi2`), Phosphor (`Pi`), Bootstrap (`Bs`), Remix (`Ri`), and Simple Icons (`Si`) for brand logos such as WhatsApp, Shopify or Instagram.

- Find the exact icon instead of settling for a near match: `node ~/joyboy/web/icon.mjs search <word> [set]` lists every name containing the word. Search a few words for the same idea (cart, bag, basket) and pick the one that says it best. Run several searches in parallel.
- Use icons by export name: `film.icons([("LuRocket", "Fast launch", "live in weeks"), ...], title=...)` for a grid of features that pop in, and `film.put_icon(img, "LuCheck", cx, cy, size, color)` inside a `custom` scene. Write `set/Name` when two sets share a name (`fa6/FaRocket`).
- Keep one set per video for the general icons so line weight and style match (Lucide or Tabler suit most modern looks); brand logos come from Simple Icons.
- Icons are rendered once and cached in `~/joyboy/icons/`.

**Animated icons: Lucide through a web scene.** When an icon should move (draw itself, pop, ring, bounce, beat), use the stroke icons from `lucide-static` in a `web` scene and animate them with GSAP, in the style of lucide-animated.

- Start from `~/joyboy/web/icon_anim_template.html`. A token written as two braces around `lucide:rocket` is replaced with that icon's SVG; the same form with `icon:LuRocket` inlines any react-icons icon. Browse Lucide names in `~/joyboy/web/node_modules/lucide-static/icons/`.
- Animate with `DrawSVGPlugin` (draw on), scale with a back ease (pop), short yoyo rotations (ring, wiggle), small moves (lift, bounce), all on the one paused timeline so capture is exact.
- The lucide-animated package itself plays its motions on hover through React and Motion, which cannot be stepped frame by frame, so its motions are recreated on the same Lucide icons with GSAP. Say so if the user asks for that package by name.
- Give animated icons their sounds with `sfx=[...]` on the scene (a `scribble` while drawing, a `pop` or `ding` on the accent).

## People: DiceBear characters, still or talking

Whenever a video needs a person (a customer, an owner, a presenter, a team, two people in conversation) or a small illustrated figure such as a robot or an emoji face, take it from DiceBear (dicebear.com). Do not draw people by hand and do not use stock photos of people. DiceBear is installed in the workspace and generates the SVG on this machine; nothing is sent to its website.

**Choosing a character**

- `node ~/joyboy/web/avatar.mjs styles` lists the styles with their licence and how many mouths and eyes each has. `node ~/joyboy/web/avatar.mjs options <style>` lists every option of one style (hair, skin colour, clothes, glasses, beard, mouth, eyes).
- `p = film.person("owner", style="avataaars", seed="any-words", options={...}, voice="lessac", tint="#f6e7dc")` makes one character. The same seed and options always give the same person. Set the options that matter (hair, skin, clothes) explicitly so the person suits the story and the audience, and give different people clearly different looks and card tints.
- Keep one style for everyone in a video so they look like they belong together.
- Characters are cached in `~/joyboy/avatars/`.

**Talking: `film.talk(person, line, role="Guest", prop="assets/screen.png")`**

- The person's face sits in a rounded card with a role label; the line is spoken and shown as a caption. The mouth is chosen frame by frame from how loud the narration is at that moment (closed, a little open, wide), the eyes blink, and the head nods slightly while speaking. This is loudness-driven lip sync, not exact mouth shapes per sound; say so if the user expects more.
- `prop` shows an image (a screenshot, a photo, a product) in a window above the speaker (beside, in landscape), panning slowly, so the person can talk about something.
- Give each person their own voice with `voice=` in `person()` (a Piper voice name, or an ElevenLabs voice id). Download a second Piper voice once when two people talk. Pass `voice="assets/line.mp3"` to `talk` to lip-sync to a ready recording.
- One short sentence per `talk` scene (about 8 to 14 words). For a dialogue, alternate speakers scene by scene.
- A talking style needs mouth and eye options. `avataaars` is built in (mouths `twinkle`, `default`, `smile`; eyes `default`, `closed`, `happy`). For another style pass `mouths=(closed, a little open, wide)` and `eyes=(open, blink, idle)`, then look at a contact sheet: some mouths read as sad or shocked and must be swapped. Styles with no mouth options (`openPeeps`, `notionists`, `dylan`) can only be still.
- For a person in a `custom` scene (a still portrait, a row of team faces, a reaction): `film.put_person(img, p, cx, cy, height, mouth, eyes)`.

**Rules**

- Licence: check it per style before using it. `avataaars`, `bottts`, `lorelei`, `notionists`, `openPeeps`, `pixelArt` and `thumbs` are free to use without credit. Most others (`adventurer`, `bigEars`, `bigSmile`, `micah`, `personas`, `toonHead`, `croodles`, `funEmoji`, `miniavs`) are CC BY 4.0: add the credit as a `note=` on the scene or tell the user to put it in the description.
- Illustrated speakers are not real people. Never present their lines as a real customer's review or quote; label them by role ("Guest", "Owner"), not with invented names, and add `note="Illustrated characters"` when the lines could be mistaken for testimonials.
- Do not model a character on a real, named person.

## Worlds: short films, stories and dialogues in a 3D place

When the request is a short film, a story, a skit, a dialogue between people, or an explainer told by characters in a place, build it in a world: a procedural low-poly 3D scene drawn with three.js (`web/world.js`), with people from `film.person()` whose faces talk the same way as in `film.talk()`. Do not use GSS for this; GSS draws everything in one shader and cannot carry a forest, weather and people. GSS stays for single 3D hero objects.

```python
asha = film.person("asha", seed="a", options={"top": ["bun"], "hairColor": ["2c1b18"], "skinColor": ["d08b5b"], "clothesColor": ["b3402a"], "eyebrows": ["defaultNatural"]}, voice="lessac")
ravi = film.person("ravi", seed="b", options={"top": ["shortCurly"], "skinColor": ["ae5d29"], "clothesColor": ["2f6f8f"], "eyebrows": ["default"]}, voice="ryan")
w = film.world(place="forest", time="night", weather="snow", seed=11, props=["campfire", "tent"],
               people=[(asha, "sit", {"scarf": "#e3b23c"}), (ravi, "sit", {"hairStyle": "beanie", "hat": "#7a3fb0"})])
film.intro("THE LONG NIGHT", sub="a very short film")
w.shot("crane", dur=4)                                                     # establishing shot, nobody speaks
w.shot("two", say=(asha, "Remember when a phone with a camera felt like the future?"))
w.shot("close:ravi", say=(ravi, "I remember your ringtone. The whole bus heard it."), tr="cut")
w.shot("orbit", dur=3)
film.outro("THE END")
```

**The world** is described once and stays the same in every shot (it is built from `seed`; change the seed for a different layout).

| Setting | Choices |
|---|---|
| `place` | `forest`, `street` (buildings, shops, lamps, traffic, passers-by), `village` (a Kerala village road: laterite path, coconut palms, banana plants, tiled houses, a tea shop, paddy fields), `meadow`, `beach` (sea), `snowfield` |
| `time` | `day`, `dusk`, `dawn`, `night` (sky, sun or moon, stars, light and lit windows follow) |
| `weather` | `clear`, `snow`, `rain` (monsoon), `storm` (downpour, wind, lightning), `fog` |
| `props` | `campfire` (flickering light, flames, embers), `lamp`, `tent`, `bench`, `logs` |
| `people` | `(person, "sit" or "stand", {extras})`; extras: `scarf`, `pants`, `umbrella` (a colour), `hairStyle` (`short`, `bun`, `long`, `curly`, `beanie`, `bald`), `hat` |
| `extras` | on a street, how many cars and passers-by (default 6; 0 for an empty street) |

Skin, hair and shirt colours come from the person's DiceBear options, so the 3D person matches their 2D picture. One to three people work; they stand or sit side by side, turned toward each other.

**Camera shots.** Each `w.shot(cam, ...)` is one scene, so cuts, captions, voices, `tr`, `note` and music work as in any other scene.

| `cam` | What it shows | Use it for |
|---|---|---|
| `wide` | the whole place with the people small | opening, breathing space |
| `full` | both people head to toe | walking, a fall, anything the body does |
| `crane` | starts near the people and rises up and back | first or last shot |
| `orbit` | circles slowly around them | opening, ending, a pause |
| `two` | both people, waist up | most dialogue |
| `close:<name>` | one face | a punchline, a reaction, an emotional line |
| `over:<name>` | that person seen over the other's shoulder | back-and-forth dialogue |
| `fallen:<name>` | straight down at someone lying on the ground | the line after a fall |
| `low`, `top` | from the ground looking up; from high above | drama; scale |
| `prop` | close on the fire or main prop | a pause between lines |

- **Walking:** `w.shot(cam, walk=True)` makes everyone walk toward the camera while the place slides past (a walk-and-talk); pass a number for metres a second (default 1.1). The distance carries on from shot to shot, so cuts stay continuous. It suits places with a path (`village`, `street`, `forest`).
- **Falling:** `w.shot("full", say=(appu, "..."), fall=(appu, "end"))` makes that person slip and land on their back with a splash as their line ends (or pass the second of the shot instead of `"end"`). Walking stops, the other person looks down, and the faller stays on the ground in later shots; film them with `fallen:<name>`. A slide whistle, a splash and footsteps are added by themselves. Use `full` for the fall so the whole body is in frame.
- **Titles in the world:** `w.shot("wide", title="...", sub="...", role="intro")` puts big words over a shot and makes it the film's opening card; `role="outro"` does the same for the closing card. Use these instead of `film.intro` / `film.outro` when the film is in a script the built-in text cannot shape.
- **Any language on screen:** captions and titles of world shots are drawn by the browser, so Malayalam, Hindi, Tamil, Arabic and other shaped scripts come out correctly with the system's fonts. Write the line in its own script and set `Film(..., lang="ml")` so the voices match.
- `say=(person, "line")` makes that person speak: lip sync, blinks, nods, a hand gesture, and the listener turns to look. For feeling in the voices, give the people Supertonic voices and tag the lines (see "Voice-over"). The line is also the caption; pass `text=""` to hide it or `text="..."` to show other words.
- Shoot it like a film: open with `crane`, `wide` or `orbit`; play dialogue on `two`, cutting to `close` or `over` of whoever speaks or reacts (use `tr="cut"` inside a conversation, a fade only to enter or leave the world); end on `orbit`, `crane` or `prop`. Do not hold one angle for more than two lines.
- One short sentence per shot. Write lines the way people talk.
- Check before rendering: `w.still("close:ravi", "work/close.png")` renders one frame in a few seconds. Look at one still per camera you plan to use, in the shape being delivered. A full render captures about ten frames a second.
- Landscape suits worlds best. Portrait works; wide and two-shots pull back to fit, so check stills.
- Worlds need the web kit (node, Chrome, three.js; see `SYSTEM.md`) and a working GPU in the capture browser.
- Limits to say plainly if asked: people walk only toward the camera, and can slip and fall, but do not pick things up, touch, sit down or get up during a shot; bodies are simple; there are six places and five props. A new place or prop is added in `world.js` (and its sound in `ambience.py`).

## Ambience: background sound for a place

Background sound is synthesized in code by `ambience.py`, like the music; no recordings are used and nothing is downloaded.

- **Worlds add it by themselves.** A world picks its sounds from its own description: `campfire` gives fire, snow or fog gives a soft muffled wind, rain and storm give rain and wind, a beach gives waves, a street gives traffic hum and horns, a wet village gives frogs, a clear night in the open gives crickets. Walking adds footsteps and a fall adds a slip whistle and a splash. Thunder follows each lightning flash and a whoosh plays as each car passes, timed from the same rules as the picture.
- **Ambience is always subtle.** It is a quiet bed that tells the ear where we are; it must never compete with a voice or the music. A world sets it to the same low loudness whatever the place (sea, rain and traffic are no louder than a soft wind), and drops it further while anyone speaks. If the user says a background sound is too loud, lower it; never raise it to make a place feel "more real".
- The bed runs without a break under all of the world's shots, the fire is a little nearer in close shots than in wide ones, and the music drops back while the film is in the world. Adjust with `w.level` (ambience loudness: 1.0 is the subtle default, 0.5 is barely there, 0 is none, and 2.0 is the most it allows) and `w.music` (how much music stays, default 0.45; use 0.25 for a quiet, intimate scene, 0.8 when the music should lead).
- **Any other scene** can have ambience through `film.sound_layer(fn)`: `fn(score, duck)` runs when the audio is mixed. Make a sound with `Ambience(seed=...)` - `fire(sec)`, `wind(sec, strength, muffled)`, `rain(sec, heavy)`, `waves(sec)`, `stream(sec)`, `crickets(sec)`, `traffic(sec, busy)`, and the single events `thunder()` and `car_pass(direction, wet)` - and add the stereo array into `score.dry` at the scene's sample position (`scene["start"] / fps * score.sr`), with a short fade in and out. Use it for a photo of a beach, a rainy title card, a map of a city.
- Keep ambience well under the voice and under the music, in every scene. When adding it yourself through `sound_layer`, keep its level low (a gain that leaves it clearly quieter than the music), fade it in and out, and lower it further under any voice. Read the printed levels after a render: the ambience figure should be a small fraction of the music figure.
- Sounds made of noise (fire, rain, wind, waves, water, thunder) are convincing. A crowd, a market or animals cannot be synthesized well; if a scene depends on those, say so, and use a recording the user supplies through `sound_layer`.

## Charts: built in, no chart library

Charts are drawn directly by `quick.py` and animate on their own: `bars`, `columns`, `line`, `donut`, `heatmap`, plus `stat` for a single number. They take plain Python data (a dict, a list, a 2D list), use the film's palette, and work in every shape.

- Do not install matplotlib, plotly, Chart.js, D3 or any other chart library for a video. If a chart type is missing (scatter, area, gauge, stacked bars), draw it in a `custom` scene with a few OpenCV calls, following the existing chart code in `quick.py` as the pattern.
- Keep charts readable on a phone: at most about 6 bars, 3 lines, 5 donut parts, or a 7x7 heat map per scene. Split bigger data across scenes.
- Put the takeaway in the `title`, not just the topic ("Orders doubled in Q4", not "Orders").

## Maps: OpenStreetMap data

`film.map(place, ...)` draws a real street map from OpenStreetMap data, styled in code to match the film. No map tiles or map libraries are used.

- `place` is a name ("Mananchira Square, Kozhikode") or `(lat, lon)`. `radius_km` sets how much is shown: 0.5-8 for streets (buildings appear at 1.5 and under), 8-150 for a region with main roads only (areas served, several towns).
- `pins=[("Label", place), ...]` drop in one at a time. `route=[place, place, ...]` draws a line through the points; it is straight between points, not turn-by-turn directions, so say so if the user expects driving routes.
- `zoom="in" | "out" | "still"`, `style={...}` to recolour (`land`, `water`, `park`, `building`, `road`, `major`, each a `(blue, green, red)` tuple). With no style, the map is tinted with the film's dark base colour.
- Data is fetched once from the public Nominatim and Overpass services and cached in `~/joyboy/maps/`, so it needs internet the first time only. Only the place name is sent. Keep requests light: one area per scene.
- The scene adds the required credit "(c) OpenStreetMap contributors"; never remove it.
- For other map needs (country outlines, flight arcs, several cities), use `scripts/maps.py` directly in a `custom` scene: `maps.geocode`, `maps.Map(lat, lon, radius_km).render(size)`, `.px(lat, lon, size)`.

## Web animation: GSAP and its plugins

When the user asks for GSAP, or wants something that web animation does best (text split into letters or lines, SVG drawing and morphing, motion along a path, scramble text, physics, complex CSS layouts), build that part as a small web page and use it as a scene with `film.web("assets/scene.html", dur=4)`.

- GSAP and every plugin (SplitText, MorphSVGPlugin, DrawSVGPlugin, MotionPathPlugin, ScrambleTextPlugin, Flip, CustomEase, Physics2DPlugin and the rest) are installed once in `~/joyboy/web/node_modules/gsap/dist`. `SYSTEM.md` shows whether the web kit is ready.
- Start from `~/joyboy/web/web_template.html`. The rules that make capture work:
  - Build one paused timeline and expose it as `window.tl` (or provide `window.joyboy = { seek(seconds) }`). The capture moves it to an exact time for each frame, so nothing is dropped.
  - No `setTimeout`, CSS animations, autoplay or scroll triggers; everything must hang off the timeline.
  - Size everything in `vw`, `vh`, `vmin` so the same page fits portrait, landscape and square.
  - Load scripts with `{{GSAP}}/Name.min.js`; the token is replaced with the local GSAP folder. Do not load anything from the internet.
  - Use the film's own look in the page: `{{FONT_BOLD}}` and `{{FONT}}` become the film's font files (use them in `@font-face`), and `{{PALETTE:0}}`, `{{PALETTE:1}}`... become its palette colours.
- A web scene behaves like any other scene: it snaps to the beat, takes `tr`, `voice` and a caption, and gets the film finish. Mix it with the built-in scenes; use it where it adds something, not for everything, because capture is slower than the built-in scenes.
- It needs node and a Chrome-family browser. If `SYSTEM.md` shows the web kit is not ready and it cannot be made ready, build the effect with the built-in toolkit instead and tell the user.

## Which 3D to use

The skill has three 3D engines. Each has one job; pick by what the shot needs, and mix them freely in one video.

| The shot needs | Use | Why |
|---|---|---|
| People talking or moving in a place (a story, a skit, a dialogue) | **Worlds** - `film.world(...)` | procedural places, weather, talking characters, film cameras |
| A real 3D model file the user supplied (a product, object, vehicle, building, animated character) | **Models** - `film.model("file.glb")` | loads the file itself, real lighting and shadows, plays its animation |
| A simple shape with a glass, metal or jelly look, or an abstract 3D background | **GSS** - a `web` scene with `clock="virtual"` | written as a short style sheet, no model needed |
| Anything flat (type, charts, maps, icons, phones, photos) | the built-in 2D scenes | faster and sharper than any 3D |

Do not use one engine for another's job: no GSS for people, no worlds for a product model, no model scene without a model file.

## 3D models: 67.js

When the user supplies a 3D model, show it with `film.model(...)`. It is drawn by 67.js (github.com/codepawl/67.js), a small MIT-licensed 3D engine built for AI agents, installed once in the workspace.

```python
m = film.model("assets/product.glb", light="studio")        # load the model once
m.shot("turntable", dur=4, text="Meet the new one")           # every shot is one scene
m.shot("push", dur=3, tr="cut", voice="Built to last.")
m.shot("hero", dur=3, tr="cut")
```

| Setting | Choices |
|---|---|
| `cam` | `turntable` (spins round the model), `orbit` (a slow arc), `push`, `pull`, `hero` (three-quarter view with a slight drift), `low`, `top` |
| `light` | `studio`, `soft`, `sun`, `dramatic` |
| `turns`, `start`, `zoom` | how many times a turntable goes round (default 0.5); starting angle in degrees; below 1 moves closer |
| `clip`, `speed`, `loop` | which animation clip in the file plays, how fast, and whether it repeats |
| `floor`, `bg` | a ground that catches the shadow (default on); the colour behind the model |

- The camera frames the model by itself from its size, in any shape. In portrait a wide model looks small; use `zoom=0.7` or a `hero` or `push` shot, and check a still.
- **Check before rendering:** `m.still("hero", "work/hero.png")` draws one frame in well under a second. Look at one still for each camera you plan to use.
- Shots take `text`, `voice`, `pace`, `note`, `sfx` and `tr` like any scene. Cut between angles with `tr="cut"`; fade only to enter or leave the model.
- **Files:** a single `.glb` file. A `.gltf` with separate files must be packed into a `.glb` first. Copy the model into the project's `assets/`.
- It does not create models. If the user has none, say so and offer GSS shapes or a 2D treatment; never invent or download a model without asking.
- It needs the web kit (node, Chrome) and a working GPU in the capture browser, like worlds and GSS.
- 67.js is new and changes weekly, so the workspace pins one version (`SYSTEM.md` shows it). Do not update it in passing; if a newer version is needed, test a still and a short capture first. Its own MP4 export and MCP server are not used here: the skill's capture is the one route to video, so sound, captions and transitions stay the same for every scene.

## 3D scenes: GSS (GPU Style Sheets)

GSS (gss-lang.dev, npm package `gss-lang`, source at github.com/LukyVj/GSS) is "CSS for 3D scenes, compiled to a shader". A scene is written like a style sheet: an `@scene` block lists objects (`sphere#ball;`, `cube.corner * 4;`), selectors and the cascade style them (`color`, `material: glass(1.5, frosted 0.3)`, `metal(0.15)`, `jelly(0.6)`, `translate`, `rotate-y`, `scale`), and `@keyframes` with `animation` move them. The compiler turns the whole scene into one fragment shader that the GPU raymarches, so there are no meshes and no Three.js. It has about 15 shapes (sphere, cube, cylinder, cone, torus, capsule, prism, pyramid, tube, lathe, extruded `path`, and more), camera properties (`camera-angle`, `camera-distance`, `camera-spin`), sun and point lights, shadows and fog. It is embedded in a page with a `<gss-scene>` element or `mount(canvas, source)`.

**What it is needed for in a video:** real 3D that the 2D toolkit cannot do.

- a 3D object as the hero of a shot: a logo or letter extruded from its SVG path and turned in space, a glass, metal or jelly shape, a simple product-like form;
- abstract 3D backgrounds and loops (floating spheres, rings, soft shapes with real lighting, reflections and shadows);
- many identical 3D objects styled and animated together with one selector;
- a 3D look that must stay easy to edit, because the scene is a short readable style sheet rather than modelling work.

**When not to use it:** anything flat (type, charts, maps, icons, photos, screenshots, phone demos) is faster and sharper with the built-in scenes; detailed models, characters and imported 3D files are outside what it does.

**How to use it:**

- `gss-lang` is installed in the workspace (`~/joyboy/web/node_modules/gss-lang`); `SYSTEM.md` shows the version. It is an early release, so expect rough edges and check results on a contact sheet.
- Start from `~/joyboy/web/gss_template.html`: a full-page canvas, the scene's style sheet in a string, `mount(canvas, source, { adaptDpr: false, controls: false })`, then `window.joyboyReady = true`. Import with `{{GSS}}/index.js`; the token is replaced with the local package folder.
- Use it as a scene with **`film.web("assets/scene3d.html", dur=5, clock="virtual")`**. `clock="virtual"` is required. GSS runs on its own clock and offers `pause()` and `play()` but no jump-to-time, so the capture replaces the page's clock (`requestAnimationFrame`, `performance.now`) and advances it exactly one video frame at a time. Ordinary `@keyframes` then capture frame-exactly; nothing special is needed in the style sheet.
- Write the scene the way CSS is written: objects in `@scene`, classes and ids for styling, `@keyframes` for motion, variables and `calc()` for patterns (`sibling-index()` to spread copies). Read the package README (`~/joyboy/web/node_modules/gss-lang/README.md`) for exact property names before writing a scene; do not guess syntax.
- Frame the shot deliberately: set the camera (`camera-distance`, `camera-angle`, `camera-spin`) so the subject fills the frame in the shape being delivered, and check both portrait and landscape.
- Captions, sounds (`sfx=[...]`), narration and transitions work on a GSS scene like any other `web` scene. The page background shows through nowhere, so match the scene's own background and lighting to the film's palette.
- It needs a working GPU in the capture browser. If frames come out blank, very slow or unchanged from one to the next, fall back to a 2D treatment and tell the user.

**The virtual clock is general.** `clock="virtual"` also makes other self-animating pages capturable frame by frame: plain WebGL or canvas animations, and libraries that run on `requestAnimationFrame`. It has been tested with GSS; test anything else on a short capture first.

## Picture: what to use

| Need | Use |
|---|---|
| Move a camera over a still image (push, pull back, tilt, pan, snap zoom, parallax, wind sway) | `jb.cam` |
| Load artwork (any format, alpha flattened) | `jb.art` |
| Drifting particles: petals, leaves, dust, snow, embers (set colour, count, speed) | `jb.petals` |
| Birds crossing the frame | `jb.birds` |
| Retro terminal / CRT screen that types text | `jb.crt` |
| Flat colour fields, shapes, grids, tunnels, loaders (pure motion graphics) | plain NumPy/OpenCV drawing on a float canvas; see recipes |
| Motion timing (ease in/out, smoothstep, spring) | `jb.eo`, `jb.ei`, `jb.eio`, `jb.spring` |

## Type: what to use

| Need | Use |
|---|---|
| Any single line of text, centred, with soft shadow; optional auto-fit and scale animation | `jb.tmask` + `jb.put` |
| Quiet caption lines that fade and drift in | `jb.caption` |
| Text arriving one letter at a time | `jb.letters` + `jb.put_letters` |
| A specific typeface or weight (variable `.woff2`/`.ttf` supported) | `jb.font(path, size, weight)` |

## Logo / mark: what to use

| Need | Use |
|---|---|
| Find a white logo painted into an image | `jb.detect_mark` |
| Keep the logo the same size and place across many images (for fast cuts) | `jb.lock` |
| Turn a logo into a vector outline (from a painting or any logo mask) | `jb.mark_from_image`, `jb.mark_contours` |
| Draw the logo anywhere, any size, filled or outlined, rotated | `jb.dmask` |
| A line of light that draws the logo | `jb.trace` |
| Shockwave ring and particle burst from a point | `jb.impact` |

## Effects: what to use

| Need | Use |
|---|---|
| Camera shake after an impact | `jb.shake` |
| White flash | add `255 * np.exp(-u / k)` to the frame |
| Glow around a shape or text | add a Gaussian-blurred copy of its mask |
| Motion blur | `cv2.blur` with a kernel sized by velocity |
| Colour split (red/blue pulled apart) | `jb.chroma(img, px)` |
| Scan lines | `jb.scanlines(img, strength)` |
| Glitch (bands knocked sideways) | `jb.glitch(img, f, amount)` for 2-4 frames |
| Fireflies, twinkling stars (night, calm scenes) | `jb.fireflies(img, f)`, `jb.stars(img, f)` |
| Film look: bloom, lens streak, colour fringing, contrast curve, tint, warmth, saturation, vignette, grain, each with its own strength | `jb.post` (once per frame, last); in `quick.py` set it with `look=` |
| Fade to/from black or white | multiply or add after `jb.post` |

## Transitions: what to use

| Need | Use |
|---|---|
| Hard cut | switch shots on a frame number |
| Dissolve | blend two shot functions with `jb.eio` over N frames |
| Whip pan | `jb.whip(a, b, p)` over ~4 frames |
| Bloom to white, then white-in | add a rising white to the end of one shot and a falling white to the start of the next |
| Matched camera move (two shots read as one move) | end both shots on the same empty area, dissolve there, continue the motion; see recipes |
| Flash cut | hard cut plus a short white flash |
| Wipes (iris, bars, doors, pie, diagonal) | `jb.wipe(a, b, p, kind)`, or `tr="iris"` etc. on a scene |

## Audio: what to use

All from `Score` in `scripts/score.py`. Place sounds with `s.add(bus, sound, s.t(frame), pan, gain)`; `s.wet` gets reverb, `s.dry` stays punchy.

| Need | Use |
|---|---|
| Melodic instruments | `piano`, `keys` (electric piano), `bell` (music box) |
| Sustained harmony | `strings` (short notes for staccato), `choir`, `sub` (bass) |
| Big cinematic brass | `braam` |
| Drums | `taiko`, `kick`, `snare`, `hat`, `roll` (accelerating snare roll) |
| Impacts | `boom`, `crash`, `reverse_crash` |
| Tension and movement | `riser`, `whoosh` |
| Small UI sounds | `click` |
| Ambience | `wind`, `birdsong`, `hum` in `Score`; fire, rain, thunder, waves, stream, crickets, traffic in `ambience.py` (see "Ambience") |
| Mix, reverb, limiter, fades, per-section level report | `s.write(path, sections=[...])` |

Tempo, key, instrumentation and intensity are creative choices for the concept at hand. Anything not in the table (other waveforms, arps, pads, a specific sound effect) can be synthesized with NumPy and placed with `s.add` the same way.

## Output: what to use

| Need | Use |
|---|---|
| Portrait, landscape or any size | `jb.init(1080, 1920, fps)`, `jb.init(1920, 1080, fps)`, etc. |
| Preview chosen frames as one image | `python film.py sheet out.jpg 0 40 80 ...` |
| Full render (parallel) and mux with audio | `python film.py` via `jb.run(frame, total_frames, out, audio)` |

## How to work

0. Run `scripts/setup.sh`, read `SYSTEM.md`, and create `projects/<video-name>/` in the workspace. Work only inside it.
1. Run the brief (see "Brief first, then decide"), then look at the material (artwork, logo, reference video frames, the brand's own words). Decide the concept from that, not from a template.
2. Lay the film out as shots on a frame timeline. If there is music, pick a tempo where a beat is a whole number of frames so sound and picture share one grid.
3. Build `frame(f)`: one function per shot using local time `u = f - shot_start`. `frame(f)` must depend only on `f`, because chunks render in parallel and out of order.
4. Render a contact sheet and look at it before any full render; fix what you see. After the full render, check a sheet pulled from the finished MP4.
5. Write the audio against the same frame numbers, and read the printed section levels.
6. Deliver it the way "The final message" describes: the video shown first, then at most five plain lines, including what you could not verify (you cannot watch motion or hear audio).
7. Leave the project folder in order: `script.md` current with its notes, finished videos in `out/`, nothing stray.

## Requirements

Python 3 with `opencv-python`, `numpy`, `pillow`, `scipy`, and `ffmpeg` on PATH. `scripts/setup.sh` checks all of these and installs the Python packages, Piper TTS and a default voice into the workspace once. It does not install `ffmpeg`; if that is missing it says so, and you ask the user before installing it.

Web scenes, icons, people (DiceBear), worlds (three.js) and GSS also need `node` (with `npm`) and a Chrome-family browser. When both are present, `setup.sh` installs the npm packages into `web/` once. Without them the rest of the kit still works: charts, maps, type, images, phones, logos, music, narration and ambience are pure Python. Two people talking need two voices; download the second Piper voice once (see "Voice-over").
