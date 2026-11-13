# joyboy recipes

Parameter values and formulas for each technique, plus known pitfalls. These are building blocks; which ones to use, and in what order, depends on the concept. Snippets assume `import joyboy as jb`, the easing helpers `eo, ei, eio, clamp`, and `u` = frames since the shot started, `N` = shot length.

## Contents

- Camera moves
- Type
- Logo / mark
- Transitions
- Pure motion graphics
- Finishing
- Audio
- Recutting and versions
- Pitfalls

## Camera moves

`jb.cam(im, z, nx, ny, f, par, horizon, wob)`. `z=1` fits the image width; `(nx, ny)` is where it looks, in 0..1 of the image.

| Move | Formula |
|---|---|
| Slow push | `z = 1.08 + 0.16*u/N`, small drift in `nx, ny`, `par` from -14 to +14 |
| Pull back | `e = eio(u/N)`; `z = 1.75 - 0.75*e`, centre moves from the subject to (0.5, 0.5) |
| Tilt | `e = eio(u/N)`; move `ny`; raise `z` if the frame should end on one area only |
| Snap zoom | `z = base + 0.5*(1 - eo(u/11, 4)) - 0.1*u/N` |
| Fast drop / rise | `d = eo(u/26, 3)`; animate `z` and `ny` with `d` |
| Handheld drift | add small sines of `f` to `nx, ny` |

- `horizon` = where the ground starts in that image (0..1). `par` above ~25 source pixels starts to shear upright subjects.
- Upscaling softens: keep tight framings short, moving, or on low-detail areas.
- `wob` sways the bottom strip (grass, water); set 0 for images where that is wrong.

## Type

- Auto-fit a word to a width: `jb.tmask(word, 300, FONT, weight, track, maxw)`.
- Scale-in: `jb.put(..., scale=1 + 0.5*(1 - eo(u/9, 4)))` with opacity `clamp(u/3)`.
- Slow drift while held: add `0.035*u/N` to the scale.
- Letter-by-letter: `jb.put_letters(img, ls, u - start, stagger)`; it needs `len(letters)*stagger + 22` frames to finish.
- Legibility over busy or bright areas: raise `shadow` in `put`, or place text over an empty area.
- Text should stay on screen long enough to read: roughly 0.3 s per word, minimum about 1 s.

## Logo / mark

- Lock across images: `box = jb.detect_mark(img)`; `jb.lock(img, box, mark_h, cx, cy)`.
- Vectorize: `C = jb.mark_from_image(img)` or `jb.mark_contours(mask)` (rasterize an SVG large first).
- Draw: `jb.dmask(C, height, cx, cy, stroke=0, rot=0)`; composite with `img*(1-a) + colour*a`.
- Light trace: `jb.trace(C, progress, u, height, cx, cy, colours)`; progress 0..1, any duration.
- Impact: `jb.impact(img, u, cx, cy, colours)`; pair with `jb.shake(img, u)` and a flash `255*np.exp(-u/4.5)`.
- Glow: `cv2.GaussianBlur(mask, (0, 0), 36)[..., None] * 255 * amount`.
- If a background zooms while the mark sits on it, scale the mark by the same factor so they move together.

## Transitions

- **Dissolve:** `a = eio((f - start)/N)`; `img = A*(1-a) + B*a`. Works best when both frames are calm or similar.
- **Whip pan:** `jb.whip(A, B, p)` with `p` over 4 frames.
- **White:** end with `+ 255*ei((u - (N-24))/24, 2.5)`, start the next with `+ 255*(1 - eo(u/22, 2))`. Same idea with black by multiplying.
- **Matched move:** end shot A and begin shot B on the same empty area (same-colour sky, wall, black), dissolve there over ~10 frames, and continue the camera motion in B. A plain dissolve between two framings that both show subjects reads as ghosting.
- **Wipes:** build a float mask `m` in 0..1 that grows with time (radial distance for iris, `xx`/`yy` thresholds for bars and doors, `xx + yy` for diagonal, angle for pie) and blend `A*(1-m) + B*m`; feather the edge by a few pixels.
- **Glitch:** shift random horizontal bands sideways and offset colour channels for 2-4 frames.

## Pure motion graphics

No artwork needed: start from `np.full((jb.H, jb.W, 3), colour, np.float32)`.

- Kinetic type: one word per beat on alternating colour fields, with scale-in.
- Grids: tile a shape or the mark; drive each tile's colour or scale by distance from a moving centre.
- Tunnels: draw nested outlines (`jb.dmask(..., stroke=...)`) at exponentially growing sizes; advance the phase each frame.
- Loaders and counters: rectangles and text driven by a 0..1 progress value.
- Draw shapes with OpenCV at sub-pixel precision (`shift=3`, `cv2.LINE_AA`).

## Finishing

- `jb.post(img, f, bloom, grain)`: lower `bloom` if whites blow out; set `grain=0` for clean flat-colour graphics.
- Apply fades after `post`.
- CRF 20 is a good default; lower values grow the file quickly once grain is on.

## Audio

`s = Score(total_frames, fps)`; place with `s.add(bus, sound, s.t(frame), pan=0, g=gain)`.

- **Buses:** `s.wet` (reverbed) for tonal parts, cymbals, effects; `s.dry` for bass, kicks, taiko, boom.
- **Beat grid:** choose BPM so one beat is a whole number of frames (24 fps: 90 BPM = 16 frames; 30 fps: 180 BPM = 10, 200 = 9, 225 = 8).
- **Notes** are MIDI numbers (60 = middle C). Chords are tuples of notes passed to `strings`/`choir`.
- **Gains:** tonal parts 0.05-0.2, drums 0.3-0.95, one main impact up to 1.0. `write()` normalises and soft-limits.
- **Timing effects to a cut:** `riser(dur)` ends abruptly, so place it at `s.t(cut) - dur`; `reverse_crash(dur)` likewise; `whoosh` slightly before the cut it covers.
- **Typing or ticks:** one `click` per character or event at its frame.
- **Custom sounds:** build any NumPy array at `s.sr` samples per second and `s.add` it.
- **Check:** pass `sections=[(f0, f1), ...]` to `write` and read the rms/peak per section to confirm quiet and loud parts are where intended.

## People and worlds

- **Character options (avataaars):** `top` (hair or hat: `bun`, `shortCurly`, `shortFlat`, `straight01`, `bob`, `curly`, `fro`, `hijab`, `turban`, `winterHat1` ...), `hairColor`, `skinColor`, `clothing`, `clothesColor`, `eyebrows`, `accessories` + `accessoriesProbability`, `facialHair` + `facialHairProbability`. Colours are hex without `#`, each value in a list. Anything left out is picked at random from the seed, so set `eyebrows` (`default` or `defaultNatural`) or a face may look worried.
- **Mouths for talking:** closed `twinkle`, a little open `default`, wide `smile`. `disbelief`, `sad`, `concerned` and `screamOpen` read as unhappy; keep them for reactions, not speech.
- **Lip sync levels:** loudness under 0.14 of the line's 95th percentile is closed, under 0.6 a little open, above that wide; the level is held for two frames. Blink for 4 frames about every 3 seconds.
- **3D hair** follows `top`: `bun`, curly kinds, long kinds and hats map to `bun`, `curly`, `long`, `beanie`; everything else is `short`. Override with `hairStyle` in the person's extras.
- **World scale:** one unit is about a metre. People are about 1.75 tall standing; the conversation happens at the middle of the place and the camera looks from the +z side, which every place keeps open.
- **Walk and fall:** a walking shot moves the place about 1.1 m a second; a village road is about 150 m long, enough for over a minute of walking. A fall takes 0.6 s from slip to ground, the splash follows at 0.45 s, and the shot holds about 2 s after it. One fall per film reads best; set it up with a boast or a warning in the lines before.
- **Dialogue rhythm:** establishing shot 3-4 s, then one line per shot; a line needs its spoken length plus about 1 s. Cut on the change of speaker; hold a close shot for a punchline.
- **Night and storm are dark by design.** If faces are hard to read on a still, use `dusk` instead of `night`, drop the umbrellas, or add a `lamp` or `campfire`.
- **Ambience levels:** read the printed `ambience: music rms ..., ambience rms ...` line. Ambience at one to two times the music is right for a story; lower `w.level` if it is more.
- **Cost:** a still takes a few seconds; a full capture runs at about ten frames a second and is cached per shot, so changing one line re-captures only that shot.

## Look and music values

- **Look strengths** (vignette, tint, fringe, contrast, streak, warmth, sat, glow, bloom, grain): cinematic 1, 1, 1, 1, 1, 0, 1, 1, 0.8, mood; soft 0.35, 0.4, 0.3, 0.5, 0.4, 0.15, 1, 0.8, 0.8, 0.006; clean 0, 0, 0, 0.3, 0, 0, 1, 0.45, 0.15, 0; punchy 0.25, 0.2, 0.5, 1.25, 0.8, 0, 1.2, 1, 0.8, 0.004; warm 0.5, 0.3, 0.4, 0.7, 0.6, 0.6, 1.05, 1, 0.8, 0.01; cool 0.5, 0.6, 0.4, 0.8, 0.5, -0.6, 0.95, 1, 0.8, 0.01; vintage 1.2, 0.5, 1.4, 0.6, 0.3, 0.5, 0.7, 1, 0.8, 0.03; none all 0.
- **Music seed:** `seed % 3` is the arrangement, `(seed // 3) % 4` where the chord loop starts, `(seed // 12) % 3` the chord set, `(seed // 36) % 5 - 2` the key in semitones (unless `key=` is given). Seeds 0, 1, 2 give the three arrangements of the first chord set.
- **Changing only the look or the music** re-renders the frames or the audio but reuses every cached capture, voice and clip.
- **Older projects** made before looks existed used the cinematic finish and one tune per mood; add `look="cinematic"` and a fixed `music_seed` to keep them as they were, or let them pick up the new defaults on the next render.

## Recutting and versions

- Remove or reorder a scene: change the dispatcher's frame ranges and shift the audio's frame numbers by the same amount. Re-render only the chunks whose frames changed, then mux.
- Remove on-screen text but keep the scene: delete only the `put`/`caption` lines.
- Another aspect ratio: `jb.init` with the new size, then re-place text and logo and pick artwork that suits the shape; do not crop the other version. The audio is reused unchanged.
- Keep a copy of the film script before each recut.

## Pitfalls

- `frame(f)` must not depend on earlier frames; seed randomness from `f` or a constant.
- Reflected borders mirror content into gaps; fill gaps with the edge colour and feather (what `jb.lock` does).
- Inpainting an element out of a painting leaves a faint ghost.
- Colour tuples containing NumPy scalars make OpenCV drawing calls fail; convert with `float()` / `int()`.
- Check text and logo placement against the subject on a contact sheet, in every aspect ratio.
- When editing code by string replacement, assert the match is unique.
- A world shot is cached by its whole description. Changing the world (seed, people, props) re-captures every shot; changing one line re-captures one.
- `film.person()` and `film.world()` run again in every render worker; they are cached, so keep their arguments constant in the script.
- You cannot hear the result or watch motion. Say so, and rely on printed levels, frame-locked timing and contact sheets.
