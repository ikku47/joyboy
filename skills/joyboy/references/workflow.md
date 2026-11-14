# The workflow: from the first message to the finished video

This is the order of work for every video. It exists so that each video is chosen from evidence, built from the best piece available (or a new piece made for it), matches a reference exactly when one is given, and does not look or sound like the last one. **The script is written last**, after the agent knows what is trending, what the toolkit holds and what must be made.

Do not skip a step because the request looks simple. A short request ("make a reel about my coffee shop") still gets all of it, quickly: the research can be five minutes, the toolkit match one table. The plan lives in `projects/<name>/plan.md`, and a render prints whether it is complete.

```
 0  setup and read everything      1  brief          2  research        3  reference
 4  toolkit match                  5  make what is missing             6  variety
 7  script (LAST)                  8  build, check, deliver
```

## 0. Setup and read what exists (always first, 1 minute)

```bash
bash <skill>/scripts/setup.sh                 # workspace, toolkit, TOOLS.md, CATALOG.md, assets/INDEX.md
python ~/joyboy/lib/plan.py new "<video name>" [--reference <their video>]
```
Read, in this order: `SYSTEM.md` (what is installed), `TOOLS.md` (every local tool, MCP server, skill and model: what to use for what), `CATALOG.md` (every scene, theme, genre, look, grade, effect, sound and saved asset), `assets/INDEX.md` (characters, sheets, sprites and models already made), and `python lib/variety.py` (what the last videos used). You cannot choose well, or tell the user what you have, without these.

## 1. Brief (the user, one question at a time)

Follow "Brief first, then decide" in SKILL.md. Write the answers into plan.md section 1. Ask whether they have a **reference** (a video, a post, a picture, an account they love). If yes, say plainly that it will be measured and matched, not imitated loosely.

## 2. Research: what is working now (for any short-form video)

Goal: formulas, not videos to copy. Output is plan.md section 2: 3 to 5 formulas (hook shape, structure, length, caption/CTA habit), each with evidence.

1. **`ig-viral`** is the method (outlier multiple: likes against that account's followers; formulas within about 10x of the user's size). It drives the browser the user is logged in to, or takes what the user pastes. It never logs in for them.
2. **Agent Reach** reads what the browser cannot or should not: `agent-reach youtube search "<niche>"`, `agent-reach read <link>`, `agent-reach instagram profile/posts`, subtitles, Reddit, X, Bilibili and the web. Read-only; if a channel needs a login say so once and let the user log in; never log in for them. No Agent Reach: use the agent's web tools or the browser pane.
3. Look at the work itself, not only the numbers: open the best 3 to 5 posts and read the first seconds (frames), the on-screen words, the cut rhythm, the colours, the sound. Likes and followers come from the post page; hover does not show them.
4. Record each formula in the user's words: *hook formula, structure (beats), length, visual style, sound, CTA, evidence*. Copy the formula, never another creator's script, voice, footage or edit; attribute in the notes.
5. No access to Instagram at all? Public web, YouTube search and the user's own saved examples are enough; say what you could not check.

## 3. Reference accuracy (only when a reference exists)

A reference gets *measured*, then matched, then checked with numbers.

```bash
python ~/joyboy/lib/refscan.py scan <reference.mp4>        # or done for you by plan.py new --reference
```
It writes `reference/<name>/`: `reference.json` and `reference.md` (shots, exact cut times, colours per shot, camera movement, tempo, loudness), `contact.jpg` and `shots/NN.jpg` (one frame per shot), `skeleton.py` (the same shot lengths and tempo as a Film).
- **Look at `contact.jpg` and the shot frames** and fill the table in `reference.md`: what is drawn, the words verbatim, the type style, the motion and transition into each shot, the sound at that moment. The scan cannot read pictures or words; you can.
- A still image or a post screenshot: describe it the same way (layout, type, colours with hex values sampled from it, spacing).
- Decide what must match exactly (cut times, colours, tempo, structure, type style) and what may differ (the subject, the words); write both in plan.md section 3.
- Keep the shot lengths from `skeleton.py`; build real scenes in place of its stubs.
- Build the film with `Film(..., exact=True, size=(w, h), fps=...)` so scene lengths are the measured lengths; one voice per character with `voice_as=`; a long shot whose caption changes without a cut is several scenes joined with `shot=(offset, total)`.
- Tempo is only scored when the reference has music with a beat; speech-only audio is reported as 'not scored'.
- After the render: `python ~/joyboy/lib/refscan.py check out/<video>.mp4 reference/<name>/reference.json`. It prints an accuracy score (aim for 85 or more) and which part differs (duration, cut times, colours, movement, tempo). Fix and re-render until it passes, then say the score in the final message. Say plainly what the numbers cannot judge (taste, text content, whether it feels the same).
- If the reference cannot be matched with what exists, that is a gap (step 5): make the missing piece instead of approximating.

## 4. Toolkit match: use what exists, on purpose

Break the planned video into beats (hook, each middle beat, proof, CTA, close). For each beat write what it **needs** (in plain words, not scene names) and search:

```bash
python ~/joyboy/lib/catalog.py find "one word per beat hook typography"
python ~/joyboy/lib/catalog.py find "comment keyword for the link"
python ~/joyboy/lib/catalog.py show kinetic
```
Fill the table in plan.md section 4: `Beat | Needs | Match (scene / theme / genre / look / grade / fx / asset / local tool) | Exists or MAKE`. Also choose the whole-film settings here: **theme, genre, look, grade, fx, size, mood**, with a reason tied to the research and the subject (not a default). Use `TOOLS.md` for beats that need an outside tool (3D with Blender, stills with a local model, a second agent for a parallel page). Use `assets/INDEX.md` to reuse a character or model that already exists.

A match is real only if the scene does what the beat needs *as the research or reference shows it*. "Close enough" is not a match; it is a gap.

## 5. Make what is missing (instead of using something that does not fit)

For each MAKE row, build the piece and test it on a contact sheet before the script exists:

| Missing | Make it with |
|---|---|
| a scene (a layout, an animation, a UI) | `python lib/scaffold.py scene NAME` then edit `local_NAME.py`; use it with `film.extend("local_NAME.py")` |
| a background / whole look | `python lib/scaffold.py theme NAME` (a painter function) |
| a picture effect or grade | `python lib/scaffold.py fx NAME`; `Film(fx=fn)` and `Film(grade=fn)` take any function |
| a character, prop, sprite sheet, 3D model | `python lib/blender_asset.py ...` (or `scaffold.py asset`), registered in the asset library with its recipe |
| a 3D model that must look right from every angle | `blender_asset.py` (mascot, or your own script based on `blender_job.py`), then **`qa` must PASS** and the **`coverage` sheet** (nine angles) must look right; fix and repeat |
| 3D shots with real camera variety | a camera plan in section 4: at least 4 different angles (height, distance, movement), an establishing shot, one close detail; `w.still` / `m.still` for each camera |
| a still, texture or concept picture | a local image model from TOOLS.md if present; register it with `assets.py add` and the exact command and seed |
| a one-off shot | `film.custom(fn, dur)` with the `jb` helpers (recipes.md) |
| music or a sound | a genre or `film.sound_layer(...)`; or the user's own track |

- Make one thing at a time, show it on a sheet, fix it, then move on. One heavy job at a time.
- If the piece will be reused, promote it: move it into `kinds.py` / `themes.py`, add a line to SKILL.md and a catalog tag. Otherwise it stays with the project.
- Record what you made in plan.md section 5 and why nothing existing fit.

## 6. Variety: every video stands apart

```bash
python ~/joyboy/lib/variety.py                 # what the last videos used
python ~/joyboy/lib/variety.py --suggest       # themes, genres, grades and scene types not used lately
```
Write in section 6 which of **theme, genre, grade, fx, scene mix, hook formula, layout, colour** differ from the last 3 to 5 videos. A render prints `variety:` warnings (same theme as a recent video, same genre, same opening scene, scene overlap above 60%, nearly the same palette). A brand series may keep palette and logo; it still changes at least two of theme, genre and the main scene type each time.

## 7. Script (only now)

`python ~/joyboy/lib/plan.py check` must say `OK` for sections 1 to 6 (and 3 and 8 when a reference exists). Then, and only then:
- Hooks, the spoken or on-screen words and the timed beat sheet: `ig-reel` (it uses the swipe file from step 2), then `ig-human` over every line.
- Write plan.md section 7: the scene list in order with durations and options, the words, the sound. State what each scene is made with from section 4.
- Write `film.py` from it.

## 8. Build, check, deliver

1. `JOYBOY_DRAFT=1 python film.py` for a draft; contact sheet (`python film.py sheet ...`); fix what you see. Check text against `film.safe`.
2. With a reference: draft first, `refscan.py check`, fix, repeat.
3. Full render once. Check a sheet from the finished MP4. Read the printed `plan:`, `variety:`, `music:` lines.
4. Caption with `ig-caption`, then `ig-human`. (Never post, comment or DM for the user.)
5. Final message as in SKILL.md: the video first, then at most five lines: what was chosen and why (research formula, theme, genre), what was made new, the accuracy score if there was a reference, what you could not verify. The SRT file, if narration.
6. Fill plan.md section 9 and leave the project folder in order. The render has already recorded the video's fingerprint for the next variety check.

## Anti-patterns (each one means stop and go back)

- Writing `film.py` or the script before sections 1 to 6 are filled.
- Skipping research because "I know what works". Evidence beats memory; formulas change by the month.
- Using the nearest scene when the beat needs something else. Make it.
- Imitating a reference loosely, or saying "matches the reference" without a `refscan.py check` score.
- The same theme, genre and scene mix as the last video.
- Copying another creator's script, voice, footage or edit. Take the formula only.
- Installing, downloading a model, signing in or spending money without asking.
