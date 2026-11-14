"""joyboy blender_job: runs INSIDE Blender (headless). Use blender_asset.py, which calls this.

    Blender -b --factory-startup -P blender_job.py -- mascot --out DIR --name NAME [--color #f58a3a] [--anim idle] [--frames 12] [--size 256] [--views 4]
    Blender -b --factory-startup -P blender_job.py -- render --model FILE --out DIR [--mode sheet|turntable|sprites] [--anim ACTION] [--frames 12] [--size 512] [--views 4]

It builds or opens a model, lights it, and renders PNGs with a transparent background into DIR/views or DIR/frames, and (for
`mascot`) saves NAME.blend and NAME.glb. Pillow, in blender_asset.py, assembles the sheets afterwards.
The mascot is a toy-like rounded cube with two tall eyes and stubby legs: a plain, recolourable character that every video can reuse.
"""
import sys, os, math, argparse
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser(); ap.add_argument("mode"); ap.add_argument("--out", required=True); ap.add_argument("--name", default="model"); ap.add_argument("--model")
ap.add_argument("--color", default="#f58a3a"); ap.add_argument("--anim", default="idle"); ap.add_argument("--frames", type=int, default=12); ap.add_argument("--size", type=int, default=512)
ap.add_argument("--views", type=int, default=4); ap.add_argument("--render", default="sheet"); ap.add_argument("--samples", type=int, default=24)
A = ap.parse_args(argv); OUT = os.path.abspath(A.out); os.makedirs(OUT, exist_ok=True)

def rgba(h, a=1.0):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]; return (*lin, a)

def material(name, color, rough=0.5, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba(color); b.inputs["Roughness"].default_value = rough
    for key in ("Coat Weight", "Clearcoat"):
        if key in b.inputs: b.inputs[key].default_value = coat; break
    return m

def rounded_box(name, size, loc, mat, bevel=0.3, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True); md = o.modifiers.new("Bevel", "BEVEL"); md.width = min(size) * bevel; md.segments = 8; md.limit_method = "NONE"
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="Bevel")          # real geometry, so every exporter and renderer sees the rounded edges
    bpy.ops.object.shade_smooth(); bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02); bpy.ops.object.mode_set(mode="OBJECT"); o.data.materials.append(mat)
    if parent: o.parent = parent
    return o

def setup_render(size, transparent=True):
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES", "BLENDER_WORKBENCH"):
        try: sc.render.engine = eng; break
        except TypeError: continue
    if sc.render.engine == "CYCLES": sc.cycles.samples = A.samples; sc.cycles.device = "CPU"
    else:
        try: sc.eevee.taa_render_samples = A.samples
        except Exception: pass
    sc.render.resolution_x = sc.render.resolution_y = size; sc.render.resolution_percentage = 100; sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    try: sc.view_settings.view_transform = "Standard"
    except Exception: pass
    w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.8, 0.82, 0.9, 1); bg.inputs[1].default_value = 0.9

def lights(center, span):
    for nm, kind, en, loc in (("Key", "SUN", 3.2, (3, -4, 5)), ("Fill", "AREA", 220.0, (-4, -3, 2)), ("Rim", "SUN", 1.6, (-2, 4, 3))):
        d = bpy.data.lights.new(nm, kind); d.energy = en
        if kind == "AREA": d.size = 4
        o = bpy.data.objects.new(nm, d); bpy.context.collection.objects.link(o); o.location = center + Vector(loc) * (span / 2.0)
        if kind == "SUN": o.rotation_euler = (center + Vector(loc) * 0 - o.location).to_track_quat("-Z", "Y").to_euler()
        else:
            c = o.constraints.new("TRACK_TO"); t = bpy.data.objects.new(nm + "T", None); bpy.context.collection.objects.link(t); t.location = center; c.target = t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

def camera(center, span, ortho=True):
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); bpy.context.collection.objects.link(cam); bpy.context.scene.camera = cam
    if ortho: cd.type = "ORTHO"; cd.ortho_scale = span * 1.15
    else: cd.lens = 70
    t = bpy.data.objects.new("CamTarget", None); bpy.context.collection.objects.link(t); t.location = center
    c = cam.constraints.new("TRACK_TO"); c.target = t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"; return cam

def orbit(cam, center, span, deg, elev=12):
    r = span * 3.2; a = math.radians(deg); e = math.radians(elev); cam.location = center + Vector((r * math.sin(a) * math.cos(e), -r * math.cos(a) * math.cos(e), r * math.sin(e)))

def bounds():
    pts = []
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and not o.hide_render:
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    if not pts: return Vector((0, 0, 0)), 2.0
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (lo + hi) / 2, max((hi - lo).x, (hi - lo).y, (hi - lo).z)


def qa_report():
    """Measure how clean the model is. Returns {checks: [(name, level, detail)], faces, tris, objects, size}. Levels: PASS, WARN, FAIL."""
    import bmesh
    dg = bpy.context.evaluated_depsgraph_get(); checks = []; faces = tris = 0; nm = loose = zero = ngon = flipped = nouv = nomat = unapplied = 0; names = []; objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); bm = bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)      # weld: formats like glTF split vertices at UV seams, and a renderer sees them joined
        nm += sum(1 for e in bm.edges if not e.is_manifold); loose += sum(1 for v in bm.verts if not v.link_edges); zero += sum(1 for f in bm.faces if f.calc_area() < 1e-9); ngon += sum(1 for f in bm.faces if len(f.verts) > 4)
        faces += len(bm.faces); tris += sum(len(f.verts) - 2 for f in bm.faces); vol = sum(f.calc_area() * (f.normal @ f.verts[0].co) / 3.0 for f in bm.faces)
        if vol < 0 and nm == 0: flipped += 1
        nouv += 0 if len(me.uv_layers) else 1; nomat += 0 if (o.material_slots and all(s.material for s in o.material_slots)) else 1
        unapplied += 0 if (all(abs(x - 1) < 1e-4 for x in o.scale) and all(abs(x) < 1e-4 for x in o.rotation_euler)) or o.parent else 1; names.append(o.name); bm.free(); o.evaluated_get(dg).to_mesh_clear()
    c, sz = bounds(); lo_z = min((o.matrix_world @ Vector(p)).z for o in objs for p in o.bound_box) if objs else 0
    add = lambda n, ok, lvl, d: checks.append((n, "PASS" if ok else lvl, d))
    add("watertight (no open or non-manifold edges)", nm == 0, "FAIL", "%d bad edges" % nm); add("no loose vertices", loose == 0, "FAIL", "%d loose" % loose); add("no zero-area faces", zero == 0, "FAIL", "%d faces" % zero)
    add("normals point outwards", flipped == 0, "FAIL", "%d objects inside-out" % flipped); add("every object has a material", nomat == 0, "FAIL", "%d without" % nomat); add("scale and rotation applied", unapplied == 0, "FAIL", "%d objects" % unapplied)
    add("UV maps present", nouv == 0, "WARN", "%d without" % nouv); add("clean quads (few n-gons)", ngon <= faces * 0.02, "WARN", "%d n-gons" % ngon); add("polygon budget (under 150k triangles)", tris < 150000, "WARN", "%d triangles" % tris)
    add("sits on the ground (lowest point at z=0)", abs(lo_z) < 0.02 * max(sz, 1e-3), "WARN", "lowest point %.3f" % lo_z); add("sensible size (0.05 to 50 units)", 0.05 <= sz <= 50, "WARN", "%.3f units" % sz); add("objects are named (not Cube.001)", not any(n.split(".")[0] in ("Cube", "Sphere", "Cylinder", "Plane") for n in names), "WARN", ", ".join(n for n in names if n.split(".")[0] in ("Cube", "Sphere", "Cylinder", "Plane"))[:60])
    return dict(checks=checks, faces=faces, tris=tris, objects=len(objs), size=round(sz, 3))

COVERAGE = [("front", 0, 10, 50, 0.62), ("three-quarter left", -38, 14, 50, 0.62), ("three-quarter right", 38, 14, 50, 0.62), ("side", 90, 8, 50, 0.62), ("back", 180, 10, 50, 0.62), ("top down", 0, 78, 50, 0.6), ("low hero", 22, -9, 28, 0.82), ("high wide", 30, 32, 24, 0.55), ("close detail", -25, 8, 120, 1.7)]   # (name, azimuth, elevation, lens mm, how much of the frame the subject fills)
def render_coverage():
    """Nine different camera angles and lenses of the model, for review (and for planning shots): front, both three-quarters, side, back, top, a low hero angle, a high wide, a tight detail."""
    d = os.path.join(OUT, "views"); os.makedirs(d, exist_ok=True); sc = bpy.context.scene; center, span = bounds(); lights(center, span); cam = camera(center, span, ortho=False)
    for i, (nm, az, el, lens, fill) in enumerate(COVERAGE):
        cam.data.lens = lens; r = lens * span / (36.0 * fill); a = math.radians(az); e = math.radians(el); tgt = center + (Vector((0, 0, span * 0.18)) if nm == "close detail" else Vector((0, 0, 0)))
        cam.location = tgt + Vector((r * math.sin(a) * math.cos(e), -r * math.cos(a) * math.cos(e), r * math.sin(e) + (span * 0.1 if lens > 60 else 0))); sc.render.filepath = os.path.join(d, "view_%02d.png" % i); bpy.ops.render.render(write_still=True)

def build_mascot():
    bpy.ops.wm.read_factory_settings(use_empty=True); setup_render(A.size)
    root = bpy.data.objects.new("Mascot", None); bpy.context.collection.objects.link(root)
    body_m = material("Body", A.color, 0.42, 0.35); leg_m = material("Legs", A.color, 0.5, 0.2); eye_m = material("Eye", "#16141a", 0.15, 0.8); hi_m = material("Glint", "#ffffff", 0.2)
    leg_m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = tuple(c * 0.78 for c in rgba(A.color)[:3]) + (1,)
    body = rounded_box("Body", (1.0, 0.86, 0.9), (0, 0, 0.62), body_m, 0.30, root)
    legs = [rounded_box("Leg" + s, (0.2, 0.22, 0.26), (x, 0, 0.13), leg_m, 0.3, root) for s, x in (("L", -0.2), ("R", 0.2))]
    eyes = []
    for s, x in (("L", -0.2), ("R", 0.2)):
        e = rounded_box("Eye" + s, (0.08, 0.05, 0.19), (x, -0.44, 0.66), eye_m, 0.4, root); eyes.append(e)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(x + 0.006, -0.472, 0.72)); g = bpy.context.active_object; g.name = "Glint" + s; bpy.ops.object.shade_smooth(); g.data.materials.append(hi_m); g.parent = root
    fr = A.frames; sc = bpy.context.scene; sc.frame_start = 1; sc.frame_end = fr
    for i in range(fr + 1):
        t = i / fr; f = i + 1
        if A.anim == "walk":
            root.location = (0, 0, abs(math.sin(t * math.pi * 2)) * 0.07); root.rotation_euler = (0, math.sin(t * math.pi * 2) * 0.07, math.sin(t * math.pi * 2) * 0.05)
            legs[0].location.y = math.sin(t * math.pi * 2) * 0.12; legs[1].location.y = -math.sin(t * math.pi * 2) * 0.12; legs[0].location.z = 0.13 + max(0, math.sin(t * math.pi * 2)) * 0.06; legs[1].location.z = 0.13 + max(0, -math.sin(t * math.pi * 2)) * 0.06
        elif A.anim == "hop":
            h = math.sin(min(t * 1.0, 1.0) * math.pi); root.location = (0, 0, h * 0.55); sq = 1 - 0.18 * (1 - h) * (1 if t < 0.15 or t > 0.85 else 0.2); root.scale = (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq)
        else:   # idle: a gentle breath and a blink
            root.location = (0, 0, math.sin(t * math.pi * 2) * 0.025); root.scale = (1 + 0.012 * math.sin(t * math.pi * 2), 1, 1 - 0.02 * math.sin(t * math.pi * 2))
        blink = 0.12 if abs(t - 0.5) < 0.5 / fr * 1.4 else 1.0
        for e in eyes: e.scale = (1, 1, blink); e.keyframe_insert("scale", frame=f)
        for o in (root, legs[0], legs[1]):
            for p in ("location", "rotation_euler", "scale"): o.keyframe_insert(p, frame=f)
    for o in bpy.context.scene.objects:
        if o.animation_data and o.animation_data.action:
            for fc in (o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []):
                for kp in fc.keyframe_points: kp.interpolation = "BEZIER"
    sc.frame_set(1)

def load_model(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".blend": bpy.ops.wm.open_mainfile(filepath=path)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if ext in (".glb", ".gltf"): bpy.ops.import_scene.gltf(filepath=path)
        elif ext == ".fbx": bpy.ops.import_scene.fbx(filepath=path)
        elif ext == ".obj": bpy.ops.wm.obj_import(filepath=path)
        elif ext == ".stl": bpy.ops.wm.stl_import(filepath=path)
        else: raise SystemExit("unsupported model type: " + ext)
    setup_render(A.size)

def render_views(cam, center, span):
    d = os.path.join(OUT, "views"); os.makedirs(d, exist_ok=True); sc = bpy.context.scene
    for i in range(A.views):
        orbit(cam, center, span, [0, 35, 90, 180, 270, 145][i % 6] if A.views <= 6 else 360 * i / A.views); sc.render.filepath = os.path.join(d, "view_%02d.png" % i); bpy.ops.render.render(write_still=True)

def render_frames(cam, center, span, turn):
    d = os.path.join(OUT, "frames"); os.makedirs(d, exist_ok=True); sc = bpy.context.scene; n = A.frames; f0, f1 = sc.frame_start, sc.frame_end
    for i in range(n):
        if turn: orbit(cam, center, span, 360 * i / n)
        else: sc.frame_set(int(round(f0 + (f1 - f0) * i / max(n, 1)))); orbit(cam, center, span, 0)
        sc.render.filepath = os.path.join(d, "frame_%03d.png" % i); bpy.ops.render.render(write_still=True)

if A.mode == "qa":
    load_model(os.path.abspath(A.model)); import json; json.dump(qa_report(), open(os.path.join(OUT, "qa.json"), "w"))
elif A.mode == "coverage":
    load_model(os.path.abspath(A.model)); render_coverage(); import json; json.dump(qa_report(), open(os.path.join(OUT, "qa.json"), "w"))
elif A.mode == "mascot":
    build_mascot(); import json; json.dump(qa_report(), open(os.path.join(OUT, "qa.json"), "w")); bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, A.name + ".blend")); bpy.context.scene.frame_set(1)
    try: bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, A.name + ".glb"), export_format="GLB", export_animations=True, export_apply=True)
    except Exception as e: print("glb export failed:", e)
    center, span = bounds(); lights(center, span); cam = camera(center, span); bpy.context.scene.frame_set(1)
    if A.render in ("sheet", "all"): render_views(cam, center, span)
    if A.render in ("sprites", "all"): render_frames(cam, center, span, turn=False)
elif A.mode == "render":
    load_model(os.path.abspath(A.model)); center, span = bounds(); lights(center, span); cam = camera(center, span)
    acts = {a.name: a for a in bpy.data.actions}
    if A.anim in acts:
        for o in bpy.context.scene.objects:
            if o.type == "ARMATURE" or o.animation_data:
                o.animation_data_create(); o.animation_data.action = acts[A.anim]
        bpy.context.scene.frame_start, bpy.context.scene.frame_end = int(acts[A.anim].frame_range[0]), int(acts[A.anim].frame_range[1])
    if A.render == "sheet": render_views(cam, center, span)
    elif A.render == "turntable": render_frames(cam, center, span, turn=True)
    else: render_frames(cam, center, span, turn=False)
print("JOB DONE", A.mode, OUT)
