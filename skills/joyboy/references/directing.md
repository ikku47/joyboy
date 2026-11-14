# Directing a joyboy film

The craft behind the workflow. Read it before writing a treatment; it is short on purpose. A film is judged in this order: **sound, rhythm, camera, direction** (staging, performance, the arc). A frame that looks good is only where it starts.

## Shape the story
- **One subject, one goal, one turn.** Someone (or something) wants a thing, something changes, it ends differently than it began. If a beat needs explaining, cut it.
- **A hook in the first three seconds.** Something happens before any logo or title.
- **An ending that answers the opening**: the same image changed, the scale revealed, the thing done right the second time.
- **One native move.** Each medium can do one thing no other can (chalk wiped and rewritten in the same place, a stamp that shakes the page, a line that draws a scene and then floods colour). Pick the one the story needs and put it at the peak. The style's `moves` in references/styles.md are a menu; invent another if the story needs it.
- The first idea for a style is usually its cliché. Write three candidate structures before choosing.

## Treatment (before any code; this is plan.md section 7)
1. **Three candidate structures**, a few lines each, and the one chosen with the reason.
2. **Logline and arc**: one sentence, then setup, turn, ending.
3. **Benchmark**: one or two reference works for this style and topic; what to learn (composition, pacing, camera grammar, colour logic) and what not to take (characters, designs, melodies, shots, logos, fonts).
4. **Shot list**: each shot with its framing, angle, move, length and *why*. For 3D, the camera plan from "3D work".
5. **Beat sheet**, second by second.
6. **Cue map**: tempo, where each cut, key action and caption lands on the grid.
7. **Sound-design table**: for each section the ambience, the main foley (name its *material*) and the state of the music.
8. **Prove the look first**: render three style frames (one the signature shot) or, with characters, a model sheet plus two frames, from the real code. Check them against the style before the full build.

## Sound is half the film
- Every visible action has a sound, in the right material (paper, wood, metal, ink and glass all sound different): use `foley` names or `sfx=`.
- Three layers: a bed (`bed=`), foley tied to actions, music. Duck the music under voice and key sounds (it is automatic).
- **At least two real silences or near-silences** before the turn or the peak; the first sound after one should be among the most important in the film. The render warns when a long film has none.
- Use sound as a transition at least twice: the next scene's sound arrives before its picture, or the last scene's sound runs on over the cut.
- Score in the instruments of the medium (genre choice), not generic piano and strings.

## Rhythm
- Write the cue map first; the picture locks to the grid. Vary the pace: one clear acceleration or deceleration, and one breath (a held pause or a long take). One even speed means it failed.
- One action, one sound, one cut, but do not cut on every beat; leave time to see.
- **Pace for the viewer, not the clock.** Text needs about letters / 16 + 1 seconds; a title card at least three seconds. Fast is made with fewer words per screen, never by cutting before people can read. The reading check in the render enforces this.

## Camera
- At least four different setups, with real changes of framing; every shot has a reason (a push is attention, an orbit is "see the whole", a crane up is "where is this", low is power, top-down is scale or a map). 2D has a camera too: push, pull, parallax, a focus pull, a frame inside a frame.
- One signature shot people remember. Transitions are made from the medium itself (a page turn, ink spreading, a stamp), one grammar, not default fades.
- At the key moments the subject fills at least a third of the frame height, with a readable silhouette.

## Performance
- Anticipation, action, follow-through on every meaningful move; characters change emotion, they do not just slide. Blend poses; never switch a pose in an `if` (except for one deliberate comic pop).
- Check every expression at final size: worried and angry are one eyebrow flip apart.

## The failures seen most
Subject too small or hard against the edge; too dark, or a colour on itself; captions covering the subject; a gag too fast to read; blank frames in a transition; a timed effect that stops tracking the subject when the camera moves; text out of the platform's safe zone (`film.safe`).

## Before delivery
Contact sheets and 0.2 s strips of key actions; one full-speed viewing with sound; every row of the sound table is really in the mix; loudness about -14 LUFS (mastered automatically); no black frames; captions in sync. **One fix round**: fix everything the review finds in one pass, check once more, tell the user anything bigger in one line. Do not rebuild a reference or a previous film: change at least four of structure, opening, signature shot, camera path, score shape and ending.

## Copyright red lines
References teach grammar only; do not copy characters, designs, melodies, shots, logos or type. No existing works, brands or characters in the film unless the user owns them or has the right; draw fictional stand-ins. Everything third-party in a film (fonts, music, images) is listed with its source and licence.
