# Playbooks: kinds of video and the scenes that suit them

Starting points for speed, not rules. Every one of these opens with `intro` and closes with `outro` (or the opening/closing scene named in its row); the table lists what goes between and around them. The concept, order and words come from the request; change anything that does not fit. Scene names are `quick.py` methods.

| Kind of video | Typical length | Mood | Scenes that suit it |
|---|---|---|---|
| Teaser / coming soon | 10-30 s | cinematic | `crt` or `title` hook, `image` or `words`, `logo(style="trace")` with the closing words |
| Logo sting / intro / outro | 3-6 s | any | `logo` alone (`trace` or `pop`), or `title` + `logo` |
| Product or offer promo | 15-30 s | upbeat | `title` hook, `image` x2-3 with captions, `stat` for the offer, `end` with where and when |
| App or website demo | 20-45 s | tech | `title`, `phone` x2-4 with one benefit each, `bullets` recap, `end` with the link |
| Explainer / how it works | 30-90 s | calm or tech | `title`, `bullets` or one `image` per step with `voice=` narration, `end` |
| Short film / skit / dialogue between people | 20-60 s | calm or cinematic | `film.world(...)`: `crane` or `orbit` to open, `two` for dialogue with cuts to `close:<name>` and `over:<name>`, `orbit` or `prop` to end; ambience comes with the world |
| Comedy skit with a walk and a fall | 25-45 s | calm or upbeat | `wide` title shot with `walk=True`, walk-and-talk on `two` and `close`, the boast on `full` with `fall=(person, "end")`, reaction on `close`, the excuse on `fallen:<name>`, `crane` title shot to close |
| Explainer told by characters | 30-90 s | calm | `world` shots for the conversation, cut with `phone`, `image` or `bullets` for what they talk about; or `talk` with a `prop` for a simpler 2D version |
| Narrated story / documentary | 30-120 s | cinematic or calm | `image` scenes with slow moves and `voice=` on each, `quote` for key lines, `end` |
| Photo slideshow / recap / memories | 20-60 s | calm or upbeat | `title`, many `image` scenes with different `move` values, `end` |
| Testimonial / quote card | 8-20 s | calm | `quote`, optional `image` behind via `bg=`, `end` |
| Data story / results / report | 20-45 s | tech | `stat` x2-3, then `columns`, `line`, `donut` or `heatmap` as the data needs |
| Location / directions / "find us" / coverage area | 10-25 s | any | `map` with pins and a route, `end` with address and hours |
| Features / services / benefits | 10-25 s | upbeat or tech | `icons` grid (library icons), or animated Lucide icons in a `web` scene, then `end` |
| 3D object or 3D logo shot | 3-10 s | cinematic or tech | a `web` scene with a GSS scene and `clock="virtual"`, bookended by `intro` and `outro` |
| Typography-led or SVG-led piece | 5-20 s | any | `web` scenes with GSAP (SplitText, DrawSVG, MorphSVG), bookended by `intro` and `outro` |
| Announcement / event invite | 10-20 s | upbeat or cinematic | `title` (what), `words` (key facts), `end` (date and place) |
| Lyric or poem video | any | calm | `quote` or `words` per line, `music()` with the user's track |
| Highlight reel from footage | 15-60 s | upbeat | `clip` scenes cut on the beat, `title` between sections, `end` |
| Countdown / list ("top 5") | 20-45 s | upbeat | `stat` or `title` for each number, `image` for each item, `end` |
| Tutorial / steps | 30-90 s | calm | `title`, then `image` or `phone` per step with `voice=`, `bullets` summary |
| Fast-cut logo-locked reel | 5-10 s | hype | `lockcut` over images that contain the logo, then `logo` or `outro` |
| Logo-led graphic reel | 6-12 s | hype | any of `window`, `slices`, `carousel`, `grid`, `tunnel`, `loader`, with `words` between, then `outro` |
| Pure motion graphics | 5-15 s | tech or hype | `words`, `grid`, `tunnel`, `loader`, shape-wipe transitions between flat colour `title` cards, `end` |

## Choosing quickly

- **Shape:** portrait for phones and social feeds, landscape for YouTube and presentations, square or 4:5 for feed posts. If unsure, portrait.
- **Mood:** cinematic for reveals and stories, upbeat for promos and reels, calm for explainers and memories, tech for apps and data. `none` when the user supplies audio or wants silence under narration.
- **Length:** let the content decide. One idea per scene; 2-4 seconds per scene; longer when narrated.
- **Words:** take them from the user's material. Short lines read better than sentences; narration can carry the detail.
- **Colour and type:** use the brand's palette and typeface when they can be found; otherwise pick a dark base and one or two accents.
- **Images:** use what the user gave. With none, use colour, type, charts and the logo; do not invent photos.

## When scenes are not enough

Use `film.custom(fn, dur)` for a shot no scene covers, and build it from the technique tables in `SKILL.md` and the formulas in `recipes.md`. A whole film can be custom when the concept needs full control; the scene layer is for speed, not a limit.
