"""joyboy styles: one name that sets a whole look and sound, so a video starts from a considered medium instead of the default.

    Film("promo", style="risograph")            theme + look treatment + grade + music + sound bed, all at once
    Film("promo", style="risograph", genre="house")   anything you pass yourself wins over the style

A style is a bundle of choices that belong together: the background (theme), a whole-picture treatment (fx), a colour grade, a music genre, a quiet sound bed, the mood,
plus advice: which scenes suit it and a few "native moves", the things that medium can do that no other can. They are starting points for a treatment, not templates for a
story; the concept, structure and words come from the brief and the research. Browse them with `python catalog.py find "<what you want>"` or in references/styles.md.

The mediums here are common visual traditions (printing, drawing, instruments, technical drawing, film, games); each is built from this toolkit's own themes, looks,
scenes and sounds. Inspired by the idea of a toolbox of film styles made in code, as in the open Lemo-Opuscar project (https://github.com/lemomo-ai/lemo-opuscar); no text,
prompts or code of that project are used here.
"""

def S(desc, theme=None, fx=None, grade=None, genre=None, mood=None, bed=None, scenes="", moves="", family="", look=None):
    return dict(desc=desc, theme=theme, fx=fx, grade=grade, genre=genre, mood=mood, bed=bed, scenes=scenes, moves=moves, family=family, look=look)

STYLES = {
    # ---------------------------------------------------------------- printed on paper
    "risograph": S("two translucent spot inks overprinted on warm paper, coarse dots, small misregistrations", "paper", "riso", None, "mallets", "upbeat", None, "kinetic, versus, stat, countdown, highlight", "a plate arrives late and the picture snaps into register; two inks make a third where they overlap; a flat shape becomes a dot field", "print"),
    "halftone-dossier": S("a case file printed in cream and CMYK dots: heavy headlines, stamps, exhibits", "paper", "halftone", None, "jazz", "upbeat", None, "stamp, highlight, timeline, quote, countdown", "a stamp slams and shakes the page; an exhibit number rolls in; a photo resolves from dots", "print"),
    "pop-art": S("loud flat primaries and big dots, black key lines, one idea per poster", "flat", ("halftone", {"period": 12}), None, "funk", "hype", None, "stamp, kinetic, versus, stages", "a word is stamped four times in four colours; dots swell into the next scene", "print"),
    "silkscreen-poster": S("hard flat inks in stepped bands, no gradients, one colour per beat", "retro", ("bands", {"palette": ("#1b2a41", "#324a5f", "#ff6f59", "#ffd166", "#f7f0de")}), None, "afro", "upbeat", None, "wrapped, countdown, kinetic, stages", "a palette swap on the beat; registration slips and snaps", "print"),
    "woodcut": S("a relief print carved from black: light exists only where the knife cut it away", "kraft", ("engrave", {"spacing": 9, "ink": "#1a120b", "paper": "#d9c4a0", "outline": True}), None, "counterpoint", "cinematic", "room", "write, quote, timeline, sketch", "carve in a line that grows into a scene; mirror the block to read the true print", "print"),
    "engraving": S("copper-plate hatching on laid paper: lines swell and cross where it gets dark", "paper", ("engrave", {"spacing": 6}), None, "counterpoint", "calm", "room", "quote, timeline, sketch, highlight, before_after", "hatch families switch on by darkness; a roundel magnifies one detail", "print"),
    "photocopy": S("a harsh black-on-paper copy: ordered dither, no greys, edges that crawl", "paper", ("dither", {"cell": 2.5}), None, "techno", "tech", "air", "kinetic, stamp, versus, notes", "a copy of a copy of a copy, each one rougher", "print"),
    "one-bit": S("exactly two inks and a dither pattern fixed to the screen, like an old handheld", "paper", ("dither", {"ink": "#101018", "paper": "#d8e4c8", "cell": 3}), None, "chiptune", "upbeat", None, "sprite, chat, kinetic, satisfying", "the picture falls through dots into the next; an inversion strike on a hit", "print"),
    "duotone-poster": S("every picture mapped between two colours, like a two-ink gig poster", "swiss", ("duotone", {"dark": "#14213d", "light": "#fca311"}), None, "house", "hype", None, "kinetic, product, countdown, wrapped", "swap the two inks for the chorus", "print"),
    # ---------------------------------------------------------------- drawn by hand
    "chalkboard": S("a slate blackboard where chalk writes itself and one idea is taught, wiped and rewritten", "chalkboard", None, None, "lofi", "calm", "room", "write, bullets, versus, stages, stat", "write what people think, wipe it, write what is true in the same place; a chalk line sews two boards", "hand"),
    "whiteboard": S("one glossy board and a marker that writes without a hand; the camera follows the pen", "whiteboard", None, None, "mallets", "upbeat", "air", "write, versus, anatomy, bullets, timeline", "the writing leads the camera; the eraser rewinds the explanation", "hand"),
    "sketchnote": S("a page of visual notes on dot-grid paper, drawn while you watch, one colour as the thread", "dotgrid", None, None, "acoustic", "calm", None, "write, timeline, highlight, bullets, stages", "the page writes itself; one yellow follows the main idea through the page", "hand"),
    "marker-paper": S("a pad of white paper and one black marker, red for wants, blue for knowns", "paper", None, None, "mallets", "upbeat", None, "write, versus, bullets, countdown", "scribble something out and draw the true thing in the gap", "hand"),
    "urban-sketch": S("a sketchbook drawn on location: wobbly ink lines first, loose colour dropped on after", "paper", None, "sunset", "acoustic", "calm", "room", "sketch, write, image, timeline, quote", "colour arrives as blotches that miss the lines a little", "hand"),
    "stick-explainer": S("plain stick people on warm paper with one accent colour; a logic you can watch", "paper", None, None, "acoustic", "upbeat", None, "stick, versus, stages, bullets, highlight", "a held hand carries a chain reaction; the ripple runs along the line", "hand"),
    "crayon-book": S("a picture-book page in wax crayon on toothy paper with a wash that hides what the crayon left", "kraft", None, "pastel", "mallets", "calm", None, "sketch, write, image, quote", "a wash reveals the drawing it covers", "hand"),
    "pencil-plate": S("a graphite and colour-pencil study on cream paper with neat labels", "paper", ("engrave", {"spacing": 7, "ink": "#3a3a3a", "outline": False}), "pastel", "acoustic", "calm", "room", "sketch, write, timeline, anatomy", "labels appear in neat hand as the drawing builds", "hand"),
    # ---------------------------------------------------------------- instruments and screens
    "terminal": S("everything is glyphs on a phosphor screen: typed output, a cursor, status lines", "scope", ("ascii", {"cell": 10}), None, "roomtone", "tech", "ballast", "crt, kinetic, timeline, changelog, cta", "type size is the camera; the typing rhythm is the edit rhythm", "screen"),
    "oscilloscope": S("thin green lines on near black, a dotted graticule, readouts that count", "scope", None, "night", "techno", "tech", "ballast", "wire, stat, timeline, line, kinetic", "text turns into a trace; a knob zooms the whole graph", "screen"),
    "thermal-camera": S("a low-resolution heat picture: brightness read as temperature, a noisy sensor", None, ("thermal", {}), None, "roomtone", "tech", "room", "image, clip, product, stat, versus", "a split where one half is the real picture and the other the heat; an alarm threshold lights up", "screen"),
    "xray-scanner": S("a baggage-scanner image: thin things orange, middling green, thick blue, on a navy belt", None, ("xray", {}), None, "techno", "tech", "air", "image, product, versus, stat", "a scan line passes and colour follows it; filter by material", "screen"),
    "hologram-hud": S("a wireframe scanned into the air with target boxes and rolling digits", "scope", None, "teal_orange", "synthwave", "tech", "air", "wire, stat, timeline, product, kinetic", "scan growth means this is real; a target lock opens a local close-up", "screen"),
    "found-footage": S("tape recovered from an empty place: tracking, noise, a date stamp, no score", None, "vhs", "night", "roomtone", "cinematic", "tape", "kinetic, image, clip, notes, chat", "autofocus hunts; the on-screen display is part of the plot", "screen"),
    "pixel-rpg": S("chunky pixels, a limited palette, text boxes that type, menus as narration", None, "pixel", None, "chiptune", "upbeat", None, "chat, stages, versus, sprite, countdown", "the palette collapses to one colour for a shock; a save file stands in for memory", "screen"),
    "dark-keynote": S("a software launch: near-black, a hairline grid, one soft glow, snap-grid precision", "keynote", None, None, "pop", "tech", None, "kinetic, product, stat, laptop, versus", "a giant number from glyph noise; the interface assembles itself", "screen"),
    "swiss-motion": S("a modular grid, one typeface, one signal colour, movement as exact as a printing press", "swiss", None, None, "techno", "tech", None, "kinetic, countdown, timeline, stat, anatomy", "snap equals beat; extreme scale contrast between words", "screen"),
    "retro-tv": S("a television broadcast of the past: scanlines, colour fringing, a warm tint and halftone", "retro", "vhs", "sunset", "synthwave", "cinematic", "tape", "stamp, kinetic, lyrics, countdown, wrapped", "a test card, a channel change as a transition", "screen"),
    # ---------------------------------------------------------------- technical drawings
    "blueprint": S("white drafting lines on cyanotype blue, drawn in drafting order, annotations that move", "blueprint", None, None, "counterpoint", "tech", "room", "wire, timeline, changelog, stages, anatomy", "drafting order is the reveal; figure numbers are the transitions", "technical"),
    "circuit-board": S("a printed circuit board from above: copper traces, pads, silkscreen, light flowing along the copper", "circuit", None, None, "techno", "tech", "ballast", "timeline, stages, stat, changelog, wire", "the flow of what you explain becomes current along a trace", "technical"),
    "instruction-manual": S("a printed assembly manual: black line art, flat parts, arrows that drive the action", "paper", ("engrave", {"spacing": 12, "outline": True}), None, "mallets", "calm", None, "stages, bullets, product, versus, timeline", "a parts explosion lands in order; the new part is the only colour", "technical"),
    "archive-lighttable": S("old negatives, letters and clippings on a cool backlit table; a loupe finds the detail", "lighttable", None, None, "ambient", "calm", "ballast", "sketch, before_after, timeline, quote, highlight", "a negative turns positive under the loupe; the table becomes an index", "technical"),
    "data-story": S("a chart as the plot: real marks drawn one at a time on cream paper, notes pinned to numbers", "paper", None, None, "acoustic", "calm", None, "bars, line, columns, donut, stat, timeline", "one mark is one fact; the axes grow with the story", "technical"),
    # ---------------------------------------------------------------- film and light
    "silent-film": S("a silver-toned print: flicker, weave, scratches, intertitles, a piano that hurries", None, "film", "noir", "jazz", "upbeat", "room", "quote, title, kinetic, countdown, stamp", "an intertitle twist; undercranked chaos", "film"),
    "newsreel": S("a 1920s newsreel: a fanfare ident, a spinning paper, maps and fast cuts", None, "film", "bleach", "jazz", "upbeat", "tape", "stamp, countdown, timeline, quote, kinetic", "the paper spins into the lens", "film"),
    "cel-anime": S("flat cel shading with hard shadows, ink outlines, a warm backlit sky, a city-pop theme", None, ("cel", {"steps": 3}), "sunset", "citypop", "upbeat", None, "skit, sprite, kinetic, lyrics, versus", "stillness as drama; a light band sweeps a held frame", "film"),
    "tilt-shift": S("the world as a tabletop model: a narrow sharp band, saturated colour, high vantage", None, ("tiltshift", {}), None, "mallets", "calm", None, "image, clip, sprite, versus, timeline", "the sharp band slides to the thing that matters", "film"),
    "neon-night": S("a rainy night in neon: grid horizon, glowing type, wet reflections", "neon", None, "night", "synthwave", "cinematic", None, "kinetic, satisfying, lyrics, countdown, stamp", "tubes strike on in sequence; a crack drains the colour", "film"),
    "teal-orange-trailer": S("a dark, graded trailer: teal shadows, orange highlights, hits on the cut", None, None, "teal_orange", "epic", "cinematic", None, "kinetic, title, stat, countdown, quote", "silence, then the one big hit", "film"),
    "noir": S("black and white, hard contrast, a slow bass and a lot of room", None, ("film", {"tone": "#cfcfcf"}), "noir", "roomtone", "cinematic", "room", "quote, title, image, kinetic", "a single lit shape in the dark", "film"),
    # ---------------------------------------------------------------- crafted objects and layouts
    "product-studio": S("a white seamless studio, soft shadows, one hero object, very little type", "studio", None, None, "pop", "upbeat", None, "product, stat, review, before_after, versus", "the object floats and callouts draw to its parts", "layout"),
    "aurora-glass": S("slow glowing colour clouds on dark, frosted shapes, a calm premium feeling", "aurora", None, None, "ambient", "calm", "air", "kinetic, highlight, product, laptop, stat", "light moves through the type", "layout"),
    "kraft-craft": S("brown kraft paper, stamped type, hand-made packaging warmth", "kraft", None, None, "acoustic", "calm", None, "stamp, write, bullets, timeline, stat", "a stamp, then a stitched label", "layout"),
    "paper-editorial": S("cream paper and a serif: calm editorial pages, pull quotes, rules", "paper", None, None, "counterpoint", "calm", None, "quote, highlight, timeline, stat, write", "a pull quote enlarges and the rest dims", "layout"),
    "brutalist-startup": S("a thick black frame, loud colour fields, hard type, a bit rude", "brutal", None, None, "phonk", "hype", None, "kinetic, stages, versus, chat, countdown", "a word gets bigger than the frame", "layout"),
    "creator-skit": S("two toy characters, one line each under coloured name pills, a work card and a client banner", None, None, None, "lofi", "calm", None, "skit, laptop, cta, sprite, chat", "an absurd request, an earnest reply, a call to action", "layout", look="cinematic"),
    "message-story": S("a text-message conversation as the whole film, typing dots and a punchline", "brutal", None, None, None, "calm", None, "chat, kinetic, stamp, highlight", "the typing dots hold the joke", "layout"),
    "scoreboard-pop": S("candy-colour stripes, hits on a tempo grid, a countdown and a report card", "flat", None, None, "pop", "hype", None, "countdown, versus, stages, wrapped, kinetic", "call and response; a report card at the end", "layout"),
    "lyric-night": S("stacked lyrics that light word by word over a moving background, a tape look", "retro", "vhs", None, "synthwave", "cinematic", "tape", "lyrics, kinetic, satisfying, quote", "the current line lights; the rest dim", "layout"),
    "calm-loops": S("wordless hypnotic motion, soft sound, made to be watched on a loop", "aurora", None, "night", "ambient", "calm", "air", "satisfying, wire, sprite", "the loop closes on itself", "layout"),
}

def get(name):
    if name not in STYLES: raise SystemExit("joyboy: unknown style %r; choose from %s" % (name, ", ".join(STYLES)))
    return STYLES[name]

def families():
    out = {}
    for n, s in STYLES.items(): out.setdefault(s["family"], []).append(n)
    return out

def markdown():
    """references/styles.md, generated from the table above."""
    L = ["# Styles: a whole look and sound in one name", "", "`Film(name, style=\"risograph\")` sets the theme, the whole-picture treatment, the grade, the music genre, the mood and a quiet sound bed together. Anything you pass yourself wins.",
         "A style is where a treatment starts, not a template: the concept, structure, words and shots still come from the brief and the research. Each style lists the scenes that suit it and its native moves (what that medium can do that no other can).", ""]
    names = {"print": "Printed on paper", "hand": "Drawn by hand", "screen": "Instruments and screens", "technical": "Technical drawings and data", "film": "Film and light", "layout": "Crafted objects and layouts"}
    for fam, title in names.items():
        L += ["## " + title, "", "| Style | What it is | Sets | Scenes that suit it | Native moves |", "|---|---|---|---|---|"]
        for n in families().get(fam, []):
            s = STYLES[n]; sets = ", ".join(x for x in (("theme " + s["theme"]) if s["theme"] else "", ("fx " + (s["fx"][0] if isinstance(s["fx"], tuple) else s["fx"])) if s["fx"] else "", ("grade " + s["grade"]) if s["grade"] else "", ("music " + s["genre"]) if s["genre"] else "", ("bed " + s["bed"]) if s["bed"] else "") if x)
            L.append("| `%s` | %s | %s | %s | %s |" % (n, s["desc"], sets, s["scenes"], s["moves"]))
        L.append("")
    L += ["Inspired by the idea of a toolbox of film styles made in code, as in the open Lemo-Opuscar project; the styles here are written from this toolkit's own parts and share no text, prompts or code with it.", ""]
    return "\n".join(L)

if __name__ == "__main__":
    print("%d styles in %d families" % (len(STYLES), len(families())))
    for fam, ns in families().items(): print("%-10s %s" % (fam, ", ".join(ns)))
