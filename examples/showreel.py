"""joyboy showreel: a test film that uses every kind of scene the skill has (sample content throughout)."""
import os, sys, random
sys.path.insert(0, os.path.expanduser("~/joyboy/lib"))
from PIL import Image, ImageDraw, ImageFont
from quick import Film
A = "assets/"; random.seed(4)
if not os.path.exists(A + "mark.png"):                                  # a simple J mark for the reel (made once)
    im = Image.new("L", (600, 600), 255); ImageDraw.Draw(im).text((300, 290), "J", font=ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 560, index=8), fill=0, anchor="mm"); im.save(A + "mark.png")
M = A + "mark.png"; ART = [A + n + ".jpg" for n in ("meadow", "sky", "sunset", "crimson", "twilight")]
film = Film("joyboy-showreel", size="landscape", mood="tech", look="clean", palette=["#0b0e14", "#ff5a36", "#4ea3f5", "#3fb950", "#d2a8ff", "#ffd166"], voice_name="ryan")

film.crt(["joyboy showreel", "> one skill. every kind of scene."], dur=4)
film.intro("EVERYTHING\nIN ONE FILM", sub="a test of every scene the skill can make", logo=M, tr="white", dur=4, voice="This is a test film. Every scene you are about to see was made by code.")

film.title("PICTURES", sub="camera moves over still images", dur=1.6)
film.image(ART[0], text="A still image, with a moving camera", move="parallax", dur=3)
film.image(ART[2], text="Push, pull, pan and tilt", move="pan", dur=2.5, tr="cut")

film.words(["WORDS", "THAT", "HIT", "THE BEAT"], per=0.4)
film.quote("Anything you type is sized to fit its box.", by="the fit rule", dur=3)
film.bullets("Lists that arrive in order", ["One point at a time", "Each with its own sound", "Always inside the frame"], dur=4)

film.title("DATA", sub="charts that draw themselves", dur=1.6)
film.stat("1,250,000", "a counter that ticks, then rings", note="sample data")
film.columns({"Q1": 12, "Q2": 18, "Q3": 15, "Q4": 27}, title="Columns rise", note="sample data", dur=3)
film.line({"Visitors": [3, 5, 4, 8, 9, 14, 13, 19], "Leads": [1, 2, 2, 3, 5, 6, 8, 11]}, title="Lines draw themselves", labels=["Jan", "", "Mar", "", "May", "", "Jul", ""], unit="k", note="sample data", dur=3)
film.donut({"Web": 52, "Apps": 31, "Brand": 17}, title="Shares sweep round", center="100%", note="sample data", dur=3)
film.heatmap([[random.randint(0, 9) for _ in range(7)] for _ in range(5)], xlabels=list("MTWTFSS"), ylabels=["9am", "12pm", "3pm", "6pm", "9pm"], title="Heat maps light up", note="sample data", dur=3)
film.icons([("LuRocket", "Fast"), ("LuShieldCheck", "Safe"), ("LuHeart", "Loved"), ("LuZap", "Light")], title="Icons from a library", dur=3.5)
film.map("Mananchira Square, Kozhikode", radius_km=1.5, title="Real street maps", pins=[("Here", "Mananchira Square, Kozhikode")], route=["Kozhikode Beach", "Mananchira Square, Kozhikode"], dur=4)

film.title("SCREENS", sub="real pages, captured", dur=1.6)
film.browser(film.capture("https://www.gss-lang.dev/", "desktop"), url="gss-lang.dev", text="A real web page in a browser", span=(0.0, 0.3), note="example site", dur=4)
film.phone(film.capture("https://www.gss-lang.dev/", "mobile"), text="And in the phone frame", span=(0.0, 0.15), note="example site", dur=3.5)

film.title("WEB ANIMATION", sub="GSAP and animated icons", dur=1.6)
film.web(A + "gsap.html", dur=4)
film.web(A + "icons.html", dur=4, sfx=[(0.2, "scribble", 0.7), (0.55, "scribble", 0.7), (0.9, "scribble", 0.7), (1.8, "ding"), (2.0, "pop")])

film.title("THREE KINDS OF 3D", sub="shapes, models and worlds", dur=1.8)
film.web(A + "scene3d.html", dur=4, clock="virtual", text="Shapes written like a style sheet")
m = film.model(A + "ambulance.glb", light="studio")
m.shot("turntable", dur=4, text="A real 3D model file", zoom=0.75)
m.shot("push", dur=2.5, tr="cut", zoom=0.75)

film.title("PEOPLE", sub="characters that talk", dur=1.6)
asha = film.person("asha", seed="a", options={"top": ["bun"], "hairColor": ["2c1b18"], "skinColor": ["d08b5b"], "clothesColor": ["b3402a"], "clothing": ["shirtCrewNeck"], "eyebrows": ["defaultNatural"]}, voice="lessac")
ravi = film.person("ravi", seed="b", options={"top": ["shortCurly"], "skinColor": ["ae5d29"], "clothesColor": ["2f6f8f"], "clothing": ["hoodie"], "eyebrows": ["default"]}, voice="ryan", tint="#dfe9f5")
film.talk(asha, "I am an illustrated character, and my mouth moves with my voice.", role="Presenter", note="Illustrated characters")
w = film.world(place="forest", time="night", weather="snow", seed=11, props=["campfire", "tent"], people=[(asha, "sit", {"scarf": "#e3b23c"}), (ravi, "sit", {"hairStyle": "beanie", "hat": "#7a3fb0"})])
w.shot("crane", dur=4, text="A whole world, built from a description")
w.shot("two", say=(asha, "So this forest was made by code?"), tr="cut")
w.shot("close:ravi", say=(ravi, "The snow, the fire, and both of us."), tr="cut")
w.shot("orbit", dur=3, tr="cut")

film.title("REEL EFFECTS", sub="fast, graphic, on the beat", dur=1.6)
film.window(M, ART, dur=4)
film.slices(ART, dur=3)
film.carousel(["LuRocket", "LuShieldCheck", "LuHeart", "LuZap"], dur=3)
film.grid(M, dur=3)
film.tunnel(M, dur=3)
film.title("IRIS", tr="iris", dur=1.2); film.title("BARS", tr="bars", bg="#4ea3f5", dur=1.2); film.title("DOORS", tr="doors", bg="#ff5a36", dur=1.2); film.title("PIE", tr="pie", bg="#7b3fe4", dur=1.2)
film.loader(mark=M, done="ALL DONE", dur=4)

film.logo(M, text="THAT'S EVERYTHING", dur=4)
film.outro("JOYBOY", sub="one skill, every kind of video", logo=M, dur=4, voice="That is everything. One skill, every kind of video.", pace=0.95)
film.render()
