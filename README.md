# joyboy

A skill that lets an AI coding agent make finished videos entirely in code: promos, teasers, logo reveals, explainers, app demos, website tours, data stories, reels and short films, with generated music, matching sound effects and narration.

You describe the video in plain words. The agent asks a few simple questions, writes a short script of scenes, renders it on your computer, and hands you an MP4. No video model, no editor and no stock footage are involved, so every frame is exact, repeatable and easy to change.

## What it can make

| Area | What you get |
|---|---|
| Pictures | Camera moves over still images: push, pull, pan, tilt, parallax |
| Type | Titles, kinetic words, quotes, bullet lists, letter-by-letter text, all sized to fit |
| Data | Counters, bar and column charts, line charts, donuts, heat maps |
| Places | Real street maps from OpenStreetMap data, with pins and routes |
| Screens | Real web pages captured and shown in a phone frame or a browser window |
| Icons | Library icons (about 30 sets), still or animated |
| Web animation | GSAP scenes captured frame by frame |
| 3D | Simple glass and metal shapes (GSS), real model files (67.js), and procedural worlds with people (three.js) |
| People | Illustrated characters that speak with lip sync |
| Reel effects | Logo-locked fast cuts, logo window, slices, carousel, grid, tunnel, loader, shape wipes |
| Sound | Music in five moods, a sound for what each scene shows, ambience, narration in many languages |
| Shapes | Tall, wide, square and 4:5 from the same script |

## Install

Pick the line for your tool. In every case, start a new session afterwards.

**Claude Code, as a plugin** (updates through the plugin system; the skill appears as `/joyboy:joyboy`):

```bash
claude plugin marketplace add ikku47/joyboy
```

```bash
claude plugin install joyboy@joyboy
```

**Claude Code, Codex and other agents, with one command** (installs for every tool it finds on your machine):

```bash
curl -fsSL https://raw.githubusercontent.com/ikku47/joyboy/main/install.sh | bash
```

Read `install.sh` first if you prefer; it only copies the skill folder into each tool's skills folder and keeps a backup of any copy already there. To choose where it goes, clone the repository and run `bash install.sh --claude`, `--codex`, `--agents`, `--all` or `--dir <folder>`.

**Any agent that reads the Agent Skills format:**

```bash
npx skills add ikku47/joyboy
```

**Claude desktop and web apps:** download `joyboy.skill` from the [Releases](https://github.com/ikku47/joyboy/releases) page, open it in Claude and choose Save skill.

**By hand:** copy the `skills/joyboy` folder into your tool's skills folder (for Claude Code, `~/.claude/skills/joyboy`).

## Use

Ask for a video in your own words:

- "Make a 20 second teaser for my coffee shop opening on Friday."
- "Turn these five screenshots into an app demo for Instagram."
- "Explain how our booking works in a one minute video with a voice-over."

The agent asks up to ten short questions (what it is for, where it will be shown, what you have, what it should say, language, style, length, sound, how it opens and closes, anything to avoid), skipping any you have already answered. Say "you decide" to skip them all.

The first video sets up a workspace in `~/joyboy` and installs what it needs once. Every later video reuses it. Each video gets its own folder there with the finished file, the code that made it and a script you can read.

## What it needs

| Need | For |
|---|---|
| Python 3 and ffmpeg | Everything. The Python packages are installed into the workspace by the skill |
| Node and a Chrome-family browser | Icons, GSAP scenes, captured web pages, characters, worlds and 3D |
| A GPU the browser can use | Worlds and 3D scenes |
| Internet, the first time | One-time installs, voice downloads and map data |

Without Node and Chrome the rest still works: charts, maps, type, images, phones, logos, music and narration are pure Python. If [bun](https://bun.sh) is installed it is used for the JavaScript packages, which makes that step much faster.

## Honest limits

- **Tested on macOS with Apple Silicon only.** Linux and Windows are untested; default fonts, the system-voice fallback and browser paths are the likely trouble spots.
- **The agent cannot watch or hear the result.** It checks still frames and printed sound levels, then tells you what it could not verify. Watch the video before you publish it.
- **Narration** uses Piper, which is free and runs on your machine. ElevenLabs is used only if you provide your own key. Lip sync follows loudness, not exact mouth shapes.
- **3D models** must be supplied as single `.glb` files; the skill shows models, it does not create them.
- **Map routes** are straight lines between points, not driving directions.
- **Other agents:** the instructions were written for Claude Code. They name a few Claude tools (a question tool, file sending, subagents) and say what to do when those are missing, but other agents have had little testing.

## Third-party pieces

The skill downloads these into your workspace when they are first needed; none are included in this repository. Each has its own licence, which applies to your use of it.

| Piece | Used for | Licence note |
|---|---|---|
| OpenCV, NumPy, Pillow, SciPy | Drawing and sound | Open source |
| ffmpeg | Encoding | You install it yourself |
| Piper TTS and its voices | Narration | Voices have their own licences |
| GSAP | Web animation | Free to use under GSAP's standard licence |
| three.js, 67.js, gss-lang | 3D | MIT, MIT, Apache 2.0 |
| react-icons, lucide-static | Icons | Each icon set has its own licence |
| DiceBear | Characters | Some styles need a credit (CC BY 4.0) |
| OpenStreetMap data | Maps | Credit "(c) OpenStreetMap contributors" is added on screen |

## What is in the repository

```
skills/joyboy/        the skill: SKILL.md, scripts, references
.claude-plugin/       plugin and marketplace files for Claude Code
install.sh            installer for Claude Code, Codex and other agents
```

## Licence

MIT. See [LICENSE](LICENSE).
