// joyboy world: a procedural low-poly world with people, weather, time of day and camera shots, drawn with three.js.
// One JSON spec in, one deterministic picture per time out:  const w = await build(spec, canvas);  w.seek(seconds)
// spec = { place, time, weather, seed, props:[], people:[{id, pose, skin, hair, hairStyle, shirt, pants, mouths, eyes, faces}],
//          shot:{cam, dur}, speak:{id, at, env:[]}, t0, fps, extras, wind }
// Places: forest, street, village (Kerala), meadow, beach, snowfield.  Times: day, dusk, dawn, night.  Weather: clear, snow, rain, storm, fog.
// Props: campfire, lamp, tent, bench, logs.  Cameras: wide, full, two, close:<id>, over:<id>, fallen:<id>, orbit, crane, low, top, prop.
// Movement: spec.walk (metres a second: the place slides past), spec.dist0 (metres walked before this shot), spec.fall {id, at}, person.state 'down'.
import * as THREE from './node_modules/three/build/three.module.js';

const rng = s => () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const hash = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
const vnoise = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return (hash(xi, yi) * (1 - u) + hash(xi + 1, yi) * u) * (1 - v) + (hash(xi, yi + 1) * (1 - u) + hash(xi + 1, yi + 1) * u) * v; };
const C = h => new THREE.Color(h), lerp = (a, b, t) => a + (b - a) * t, sm = t => { t = Math.min(Math.max(t, 0), 1); return t * t * (3 - 2 * t); };
const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, flatShading: true, roughness: 0.9, metalness: 0, ...o });
const mesh = (g, m, x = 0, y = 0, z = 0, shadow = true) => { const o = new THREE.Mesh(g, m); o.position.set(x, y, z); o.castShadow = shadow; o.receiveShadow = true; return o; };

const TIMES = {
  day:   { top: 0x3f86d8, bot: 0xcfe6fb, sun: 0xfff1d8, sunI: 2.6, amb: 0xc4d6ff, ambI: 1.0, fog: 0xcfe3f5, dir: [0.5, 1.0, 0.45], stars: 0 },
  dusk:  { top: 0x2a2757, bot: 0xff9a5c, sun: 0xffa868, sunI: 1.9, amb: 0x9585b8, ambI: 0.75, fog: 0xc98a78, dir: [-0.9, 0.28, 0.35], stars: 0.25 },
  dawn:  { top: 0x5279b3, bot: 0xffd2ac, sun: 0xffd6ae, sunI: 1.8, amb: 0xaab9da, ambI: 0.8, fog: 0xe6c8b6, dir: [0.9, 0.3, 0.35], stars: 0.1 },
  night: { top: 0x040716, bot: 0x18244a, sun: 0x93abff, sunI: 0.9, amb: 0x4a5c94, ambI: 1.15, fog: 0x0c1429, dir: [-0.45, 0.9, 0.25], stars: 1 },
};
const WEATHER = { clear: { fog: 0.010, dim: 1 }, snow: { fog: 0.028, dim: 0.8 }, rain: { fog: 0.030, dim: 0.6 }, storm: { fog: 0.040, dim: 0.42 }, fog: { fog: 0.075, dim: 0.7 } };

export async function build(spec, canvas) {
  const W = canvas.width, H = canvas.height, R = rng(spec.seed ?? 1), T = TIMES[spec.time] || TIMES.day, WX = WEATHER[spec.weather] || WEATHER.clear;
  const snow = spec.weather === 'snow' || spec.place === 'snowfield', wet = spec.weather === 'rain' || spec.weather === 'storm', night = spec.time === 'night';
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true }); renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = night ? 1.25 : 1.0;
  const scene = new THREE.Scene(), ticks = [];                       // ticks: functions (t, frame) run every frame
  const fogC = C(T.fog).multiplyScalar(lerp(1, WX.dim, 0.6)); if (wet || spec.weather === 'fog') fogC.lerp(C(night ? 0x10141c : 0x8b939c), 0.6);
  scene.fog = new THREE.FogExp2(fogC, WX.fog * (night ? 1.25 : 1)); scene.background = fogC.clone();

  // ----- sky, sun or moon, stars -----
  const skyG = new THREE.SphereGeometry(150, 24, 12), sc = [], top = C(T.top).multiplyScalar(WX.dim), bot = C(T.bot).multiplyScalar(lerp(1, WX.dim, 0.7)); if (wet) { top.lerp(C(0x20242c), 0.6); bot.lerp(C(night ? 0x151a24 : 0x6f7884), 0.7); }
  for (let i = 0; i < skyG.attributes.position.count; i++) { const k = sm(skyG.attributes.position.getY(i) / 90 + 0.08), c = bot.clone().lerp(top, k); sc.push(c.r, c.g, c.b); }
  skyG.setAttribute('color', new THREE.Float32BufferAttribute(sc, 3)); const sky = new THREE.Mesh(skyG, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false })); scene.add(sky);
  const sunDir = new THREE.Vector3(...T.dir).normalize(), clearSky = !wet && spec.weather !== 'fog';
  if (clearSky || spec.weather === 'snow') { const disc = new THREE.Mesh(new THREE.CircleGeometry(night ? 5 : 7, 24), new THREE.MeshBasicMaterial({ color: night ? 0xf2f0dc : T.sun, fog: false, transparent: true, opacity: spec.weather === 'snow' ? 0.55 : 1 })); disc.position.copy(sunDir).multiplyScalar(140); disc.lookAt(0, 0, 0); scene.add(disc); }
  if (T.stars && clearSky) { const p = []; for (let i = 0; i < 700; i++) { const a = R() * Math.PI * 2, e = Math.acos(R() * 0.95); p.push(Math.sin(e) * Math.cos(a) * 145, Math.cos(e) * 145 + 4, Math.sin(e) * Math.sin(a) * 145); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.6, sizeAttenuation: false, fog: false, transparent: true, opacity: 0.85 * T.stars }))); }
  const amb = new THREE.HemisphereLight(C(T.amb), C(snow ? 0x8b97b0 : 0x3a3328), T.ambI * lerp(1, WX.dim, 0.5)); scene.add(amb);
  const sun = new THREE.DirectionalLight(C(T.sun), T.sunI * WX.dim); sun.position.copy(sunDir).multiplyScalar(40); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 90 }); sun.shadow.bias = -0.0015; sun.shadow.normalBias = 0.04; scene.add(sun);
  { const fill = new THREE.DirectionalLight(C(night ? 0x8fa2e0 : 0xffffff), night ? 0.7 : 0.35); fill.position.set(2, 3, 12); scene.add(fill); }   // soft light from the open (camera) side so faces never go black

  // ----- ground -----
  const street = spec.place === 'street', beach = spec.place === 'beach', village = spec.place === 'village';
  const groundCol = snow ? 0xe9eff7 : village ? 0x4c8c3c : street ? 0x2d3036 : beach ? 0xe2c990 : spec.place === 'meadow' ? 0x6fae4a : 0x4d7a3c;
  const height = (x, z) => { if (street) return 0; if (village) return sm((Math.abs(x) - 3.4) / 5) * (vnoise(x * 0.15 + 3, z * 0.15) - 0.45) * 0.45; if (beach) return (z < -6 ? (z + 6) * 0.075 : 0) + (vnoise(x * 0.2, z * 0.2) - 0.5) * 0.3 * sm((Math.hypot(x, z) - 4) / 6); const d = Math.hypot(x, z), flat = sm((d - 5) / 9); return flat * (vnoise(x * 0.09 + 7, z * 0.09 + 3) * 3.2 + vnoise(x * 0.3, z * 0.3) * 0.6 - 0.9) + (1 - flat) * (vnoise(x * 0.6, z * 0.6) - 0.5) * 0.08; };
  { const g = new THREE.PlaneGeometry(160, 160, 80, 80); g.rotateX(-Math.PI / 2); const p = g.attributes.position; for (let i = 0; i < p.count; i++) p.setY(i, height(p.getX(i), p.getZ(i)));
    g.computeVertexNormals(); const m = mesh(g.toNonIndexed(), mat(groundCol, wet && !village ? { roughness: 0.35, metalness: 0.1, color: C(groundCol).multiplyScalar(0.7) } : {}), 0, 0, 0, false); m.geometry.computeVertexNormals(); scene.add(m); }

  // ----- reusable pieces -----
  const trunkM = mat(0x5b4030), pineM = mat(snow ? 0x2f5a44 : 0x2f6b3c), leafM = [mat(0x4f8f3a), mat(0x6aa544), mat(spec.time === 'dusk' ? 0xc9843a : 0x3f7d3a)], snowM = mat(0xf4f8ff), rockM = mat(snow ? 0x8d97a6 : 0x7c7f86);
  function tree(x, z, s, kind) { const g = new THREE.Group(); g.position.set(x, height(x, z) - 0.05, z); g.rotation.y = R() * 6.28; g.scale.setScalar(s);
    if (kind === 'pine') { g.add(mesh(new THREE.CylinderGeometry(0.12, 0.18, 1.0, 6), trunkM, 0, 0.5, 0)); for (let i = 0; i < 3; i++) { const r = 1.05 - i * 0.27, y = 1.25 + i * 0.75; g.add(mesh(new THREE.ConeGeometry(r, 1.25, 7), pineM, 0, y, 0)); if (snow) g.add(mesh(new THREE.ConeGeometry(r * 0.72, 0.62, 7), snowM, 0, y + 0.36, 0, false)); } }
    else { g.add(mesh(new THREE.CylinderGeometry(0.13, 0.2, 1.5, 6), trunkM, 0, 0.75, 0)); const m = snow ? snowM : leafM[Math.floor(R() * 3)]; for (let i = 0; i < 3; i++) g.add(mesh(new THREE.IcosahedronGeometry(0.75 - i * 0.12, 0), m, (R() - 0.5) * 0.7, 1.85 + i * 0.42, (R() - 0.5) * 0.7)); }
    scene.add(g); return g; }
  const rock = (x, z, s) => { const m = mesh(new THREE.DodecahedronGeometry(s, 0), rockM, x, height(x, z) + s * 0.3, z); m.rotation.set(R() * 3, R() * 3, R() * 3); m.scale.y = 0.65; scene.add(m); if (snow) { const c = mesh(new THREE.DodecahedronGeometry(s * 0.8, 0), snowM, x, height(x, z) + s * 0.62, z, false); c.scale.y = 0.35; scene.add(c); } };
  const glowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(255,255,255,0.55)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
  const lights = [];                                                  // warm lights that flicker or glow: {light, base, flicker}
  function lamp(x, z, h = 3.4) { const g = new THREE.Group(); g.position.set(x, height(x, z), z); const pm = mat(0x23262b, { roughness: 0.6 });
    g.add(mesh(new THREE.CylinderGeometry(0.06, 0.09, h, 6), pm, 0, h / 2, 0)); g.add(mesh(new THREE.BoxGeometry(0.34, 0.34, 0.34), new THREE.MeshBasicMaterial({ color: night || spec.time === 'dusk' || wet ? 0xffe2a8 : 0xd8d8d0 }), 0, h + 0.1, 0, false)); g.add(mesh(new THREE.ConeGeometry(0.34, 0.18, 4), pm, 0, h + 0.36, 0));
    if (night || spec.time === 'dusk' || wet) { const l = new THREE.PointLight(0xffc878, 26, 16, 1.8); l.position.set(0, h, 0); g.add(l); lights.push({ light: l, base: 26, flicker: 0.03 });
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xffd08a, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending })); s.scale.setScalar(2.6); s.position.set(0, h + 0.1, 0); g.add(s); }
    scene.add(g); return g; }

  // ----- places -----
  const anchor = new THREE.Vector3(0, 0, 0); let seatY = 0;
  if (village) {                                                      // a Kerala village road: laterite path, coconut palms, banana plants, tiled houses, a tea shop, paddy fields
    const mudM = mat(0x7d4630, { roughness: 0.45 }), lat = mat(0x9a5238), wallCols = [0xf2ead8, 0xe9d9a6, 0xcfe3ea, 0xf0c9b0, 0xdfe8c8], tileM = mat(0xa8432b), woodM = mat(0x5a3a26), sway = [];
    { const g = new THREE.PlaneGeometry(4.8, 170, 4, 60); g.rotateX(-Math.PI / 2); const p = g.attributes.position; for (let i = 0; i < p.count; i++) { p.setY(i, 0.03 + (vnoise(p.getX(i) * 0.9, p.getZ(i) * 0.5) - 0.5) * 0.05); if (Math.abs(p.getX(i)) > 2.3) p.setX(i, p.getX(i) + (vnoise(p.getZ(i) * 0.3, 2) - 0.5) * 0.8); }
      const m = mesh(g.toNonIndexed(), mudM, 0, 0, 0, false); m.geometry.computeVertexNormals(); scene.add(m); }
    if (wet) for (let i = 0; i < 34; i++) { const pd = mesh(new THREE.CircleGeometry(0.35 + R() * 0.7, 9), new THREE.MeshStandardMaterial({ color: 0x8d9ba6, roughness: 0.12, metalness: 0.25 }), (R() - 0.5) * 3.6, 0.075, -70 + R() * 145, false); pd.rotation.x = -Math.PI / 2; pd.scale.y = 0.55 + R() * 0.4; scene.add(pd); }
    const palm = (x, z, s) => { const g = new THREE.Group(), tm = mat(0x7a6652), lean = 0.05 + R() * 0.12; g.position.set(x, height(x, z), z); g.scale.setScalar(s); g.rotation.y = R() * 6.28; let px = 0, py = 0;
      for (let k = 0; k < 7; k++) { const seg = mesh(new THREE.CylinderGeometry(0.15 - k * 0.008, 0.17 - k * 0.008, 1.0, 6), tm, px, py + 0.5, 0); seg.rotation.z = -lean * k * 0.5; g.add(seg); px += Math.sin(lean * k * 0.5) * 1.0; py += Math.cos(lean * k * 0.5) * 0.98; }
      const crown = new THREE.Group(); crown.position.set(px, py, 0); crown.userData.p = R() * 6.28; g.add(crown); sway.push(crown);
      for (let k = 0; k < 9; k++) { const f = new THREE.Group(), leaf = mesh(new THREE.ConeGeometry(0.34, 3.0, 4), mat(k % 2 ? 0x2f7d3a : 0x3f9447), 0, 1.5, 0); leaf.scale.z = 0.12; f.add(leaf); f.rotation.y = k / 9 * 6.283 + R() * 0.3; f.rotateZ(-(1.15 + R() * 0.75)); crown.add(f); }
      for (let k = 0; k < 3; k++) crown.add(mesh(new THREE.IcosahedronGeometry(0.16, 0), mat(0x6f7a2f), Math.cos(k * 2.1) * 0.22, -0.18, Math.sin(k * 2.1) * 0.22)); scene.add(g); };
    const banana = (x, z) => { const g = new THREE.Group(); g.position.set(x, height(x, z), z); g.add(mesh(new THREE.CylinderGeometry(0.09, 0.13, 1.5, 6), mat(0x8fae4a), 0, 0.75, 0));
      for (let k = 0; k < 5; k++) { const f = new THREE.Group(); f.position.y = 1.45; f.add(mesh(new THREE.PlaneGeometry(0.55, 1.9), new THREE.MeshStandardMaterial({ color: 0x57b04a, side: THREE.DoubleSide, flatShading: true, roughness: 0.8 }), 0, 0.95, 0)); f.rotation.y = k / 5 * 6.283 + R(); f.rotateZ(-(0.5 + R() * 0.7)); g.add(f); } scene.add(g); };
    const house = (x, z, side) => { const g = new THREE.Group(), w = 5 + R() * 2, d = 4.2 + R(), h = 2.7, wm = mat(wallCols[Math.floor(R() * wallCols.length)]); g.position.set(x, height(x, z) + 0.25, z); g.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;   // the front faces the road
      g.add(mesh(new THREE.BoxGeometry(w + 1.2, 0.5, d + 2.6), lat, 0, 0, 0.6)); g.add(mesh(new THREE.BoxGeometry(w, h, d), wm, 0, h / 2 + 0.25, 0));
      const roof = mesh(new THREE.ConeGeometry(1, 1.7, 4), tileM, 0, h + 1.05, 0); roof.rotation.y = Math.PI / 4; roof.scale.set((w + 1.4) * 0.72, 1, (d + 1.4) * 0.72); g.add(roof);
      const ver = mesh(new THREE.BoxGeometry(w + 1.0, 0.12, 2.2), tileM, 0, h - 0.25, d / 2 + 1.0); ver.rotation.x = 0.32; g.add(ver);
      for (const px of [-w / 2, 0, w / 2]) g.add(mesh(new THREE.CylinderGeometry(0.09, 0.09, 2.1, 6), woodM, px * 0.92, 1.3, d / 2 + 1.8));
      g.add(mesh(new THREE.BoxGeometry(0.9, 1.9, 0.08), woodM, 0, 1.2, d / 2 + 0.03)); for (const px of [-1, 1]) g.add(mesh(new THREE.BoxGeometry(0.8, 0.9, 0.08), mat(0x3d5a66), px * w * 0.3, 1.6, d / 2 + 0.03)); scene.add(g); };
    { const g = new THREE.Group(); g.position.set(5.0, 0.05, -9); g.rotation.y = -Math.PI / 2;                                         // tea shop
      for (const [px, pz] of [[-1.6, 1.1], [1.6, 1.1], [-1.6, -1.1], [1.6, -1.1]]) g.add(mesh(new THREE.CylinderGeometry(0.06, 0.06, 2.4, 5), woodM, px, 1.2, pz));
      const tin = mesh(new THREE.BoxGeometry(4.0, 0.06, 3.2), mat(0x7f8a93, { roughness: 0.4, metalness: 0.5 }), 0, 2.45, 0.2); tin.rotation.x = 0.16; g.add(tin);
      g.add(mesh(new THREE.BoxGeometry(3.0, 0.95, 0.6), mat(0x2f6f8f), 0, 0.48, 0.9), mesh(new THREE.BoxGeometry(3.2, 2.2, 0.1), mat(0xe9d9a6), 0, 1.1, -1.1));
      for (let k = 0; k < 5; k++) g.add(mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.3, 7), mat([0xd9a441, 0xc2410c, 0xe8e2c8, 0x8a5a2b, 0xd9a441][k], { roughness: 0.3 }), -1.1 + k * 0.55, 1.1, 0.9));
      g.add(mesh(new THREE.BoxGeometry(2.2, 0.08, 0.4), woodM, 0, 0.45, 2.0)); for (const px of [-0.9, 0.9]) g.add(mesh(new THREE.BoxGeometry(0.08, 0.45, 0.36), woodM, px, 0.22, 2.0));
      g.add(mesh(new THREE.SphereGeometry(0.09, 6, 5), new THREE.MeshBasicMaterial({ color: 0xffe2a8 }), 0, 2.05, 0.6, false)); const l = new THREE.PointLight(0xffc878, 9, 9, 1.8); l.position.set(0, 2.0, 0.6); g.add(l); lights.push({ light: l, base: 9, flicker: 0.04 }); scene.add(g); }
    for (let z = -70; z < 80; z += 13 + R() * 5) if (Math.abs(z + 9) > 6) house(9.0 + R() * 3, z, 1);
    for (let z = -55; z < 80; z += 34 + R() * 12) house(-10 - R() * 2, z, -1);
    for (let z = -75; z < 80; z += 12) for (let x = -17; x > -50; x -= 10.5) { if (R() < 0.15) continue; scene.add(mesh(new THREE.BoxGeometry(10, 0.3, 11.4), R() < 0.3 ? new THREE.MeshStandardMaterial({ color: 0x6f8f8a, roughness: 0.1, metalness: 0.6 }) : mat(R() < 0.5 ? 0x86c64f : 0x9bd15a), x, 0.0, z, false)); }
    for (let i = 0; i < 56; i++) { const sx = R() < 0.5 ? -1 : 1; palm(sx * (3.6 + R() * (sx < 0 ? 12 : 5)), -74 + R() * 152, 0.85 + R() * 0.5); }
    for (let i = 0; i < 30; i++) { const sx = R() < 0.5 ? -1 : 1; banana(sx * (3.3 + R() * 3.4), -74 + R() * 152); }
    for (const sx of [-1, 1]) for (let z = -75; z < 80; z += 7 + R() * 6) { if (R() < 0.45 || (sx > 0 && Math.abs(z + 9) < 4)) continue; scene.add(mesh(new THREE.BoxGeometry(0.3, 0.7, 3 + R() * 3), lat, sx * 3.05, 0.35, z)); }
    for (let z = -70; z < 80; z += 18) { scene.add(mesh(new THREE.CylinderGeometry(0.07, 0.09, 6, 6), mat(0x4a4f55), -3.5, 3, z), mesh(new THREE.BoxGeometry(1.4, 0.08, 0.08), mat(0x4a4f55), -3.5, 5.6, z)); }
    ticks.push(t => { for (const c of sway) c.rotation.z = Math.sin(t * 1.3 + c.userData.p) * (wet ? 0.07 : 0.03); });
  } else if (street) {
    anchor.set(0, 0.16, -4.6); const walkM = mat(wet ? 0x4a4d52 : 0x8a8d92, wet ? { roughness: 0.4 } : {}), lineM = new THREE.MeshBasicMaterial({ color: 0xd9d4bd });
    for (const z of [-5.6, 5.6]) scene.add(mesh(new THREE.BoxGeometry(160, 0.16, 4.2), walkM, 0, 0.08, z, false));
    for (let x = -60; x < 60; x += 4) scene.add(mesh(new THREE.BoxGeometry(1.8, 0.01, 0.14), lineM, x, 0.012, 0, false));
    const facade = (w, h, col, lit) => { const cols = Math.max(2, Math.round(w / 1.7)), rows = Math.max(3, Math.round(h / 2.0)), cw = 48, ch = 56, mk = () => { const c = document.createElement('canvas'); c.width = cols * cw; c.height = rows * ch; return c; };
      const a = mk(), b = mk(), xa = a.getContext('2d'), xb = b.getContext('2d'); xa.fillStyle = '#' + C(col).getHexString(); xa.fillRect(0, 0, a.width, a.height); xb.fillStyle = '#000'; xb.fillRect(0, 0, b.width, b.height);
      xa.fillStyle = 'rgba(0,0,0,0.18)'; for (let j = 1; j < rows; j++) xa.fillRect(0, j * ch - 2, a.width, 3);                                   // floor lines
      for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) { const shop = j === rows - 1, x = i * cw + (shop ? 5 : 12), y = j * ch + (shop ? 14 : 13), ww = cw - (shop ? 10 : 24), hh = ch - (shop ? 14 : 27), on = shop ? lit > 0 : R() < lit;
        xa.fillStyle = on ? '#f0d49a' : (night ? '#182033' : wet ? '#5f7486' : '#86a9c2'); xa.fillRect(x, y, ww, hh); xa.strokeStyle = 'rgba(0,0,0,0.4)'; xa.lineWidth = 2; xa.strokeRect(x, y, ww, hh); if (!shop) { xa.fillStyle = 'rgba(255,255,255,0.25)'; xa.fillRect(x - 2, y + hh, ww + 4, 3); }
        if (on) { xb.fillStyle = shop ? '#ffd58a' : ['#ffd98a', '#ffe9b8', '#ffc56e', '#cfe6ff'][Math.floor(R() * 4)]; xb.fillRect(x, y, ww, hh); } }
      const ta = new THREE.CanvasTexture(a), tb = new THREE.CanvasTexture(b); ta.colorSpace = tb.colorSpace = THREE.SRGBColorSpace; ta.anisotropy = 4;
      return new THREE.MeshStandardMaterial({ map: ta, emissiveMap: tb, emissive: 0xffffff, emissiveIntensity: lit ? 0.9 : 0, roughness: 0.9 }); };
    const cols = [0x9a6a58, 0x74808c, 0xa8936f, 0x5f6975, 0x8f6a5c, 0x7d8c7a, 0xb39d86, 0x6b5d70];
    for (const side of [-1, 1]) { let x = -62; while (x < 62) { const w = 5 + R() * 5, h = 6 + R() * 13, d = 7 + R() * 3, z = side * (7.7 + d / 2), col = cols[Math.floor(R() * cols.length)];
        const lit = night ? 0.45 : spec.time === 'dusk' || wet ? 0.3 : 0, m = facade(w, h, col, lit), plain = mat(C(col).multiplyScalar(0.85)), roofM = mat(C(col).multiplyScalar(0.55));
        scene.add(mesh(new THREE.BoxGeometry(w, h, d), [plain, plain, roofM, plain, m, m], x + w / 2, h / 2, z));
        scene.add(mesh(new THREE.BoxGeometry(w + 0.2, 0.3, d + 0.2), roofM, x + w / 2, h + 0.15, z));                                          // parapet
        if (R() < 0.6) scene.add(mesh(new THREE.BoxGeometry(1.2 + R(), 0.9 + R() * 0.8, 1.2 + R()), mat(0x55585e), x + w * (0.3 + R() * 0.4), h + 0.75, z - side * d * 0.2));   // roof tank
        const aw = mesh(new THREE.BoxGeometry(w * 0.86, 0.1, 1.4), mat([0xc2410c, 0x2f6f8f, 0x8a2f3c, 0x3f7d57, 0xb7791f][Math.floor(R() * 5)]), x + w / 2, 2.55, side * 7.1); aw.rotation.x = side * 0.22; scene.add(aw); x += w + 0.25; } }
    for (let x = -42; x <= 42; x += 12) { lamp(x + 3, -3.9); lamp(x - 3, 3.9); }
    if (wet) for (let i = 0; i < 14; i++) { const p = mesh(new THREE.CircleGeometry(0.5 + R() * 0.9, 9), new THREE.MeshStandardMaterial({ color: 0x1a1e26, roughness: 0.05, metalness: 0.9 }), (R() - 0.5) * 40, 0.02, (R() - 0.5) * 6, false); p.rotation.x = -Math.PI / 2; p.scale.y = 0.6; scene.add(p); }
    const carM = [0xc0392b, 0x2e86c1, 0xf1c40f, 0xecf0f1, 0x27ae60, 0x34495e], cars = [];           // traffic
    for (let i = 0; i < (spec.extras ?? 6); i++) { const g = new THREE.Group(), dirn = i % 2 ? 1 : -1, bm = mat(carM[Math.floor(R() * carM.length)], { roughness: 0.5 });
      g.add(mesh(new THREE.BoxGeometry(2.3, 0.55, 1.1), bm, 0, 0.5, 0)); g.add(mesh(new THREE.BoxGeometry(1.2, 0.45, 1.0), mat(0x1c2530, { roughness: 0.3 }), -0.1, 0.98, 0));
      for (const [wx, wz] of [[-0.75, 0.56], [0.75, 0.56], [-0.75, -0.56], [0.75, -0.56]]) { const wh = mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.16, 8), mat(0x111111), wx, 0.24, wz); wh.rotation.x = Math.PI / 2; g.add(wh); }
      for (const wz of [0.36, -0.36]) g.add(mesh(new THREE.BoxGeometry(0.06, 0.14, 0.22), new THREE.MeshBasicMaterial({ color: 0xfff3c4 }), 1.16, 0.55, wz, false), mesh(new THREE.BoxGeometry(0.06, 0.12, 0.22), new THREE.MeshBasicMaterial({ color: 0xff3b30 }), -1.16, 0.55, wz, false));
      if (night || wet) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xfff0c0, transparent: true, opacity: 0.6, depthWrite: false, blending: THREE.AdditiveBlending })); s.scale.setScalar(1.8); s.position.set(1.3, 0.55, 0); g.add(s); }
      g.rotation.y = dirn > 0 ? 0 : Math.PI; g.position.z = dirn > 0 ? 1.7 : -1.7; scene.add(g); cars.push({ g, dirn, x0: (hash(i * 3.1 + (spec.seed ?? 1), 17) - 0.5) * 110, v: 5 + hash(i * 5.3 + (spec.seed ?? 1), 29) * 4 }); }   // from hash, not R(), so the sound code can compute when each car passes
    ticks.push(t => { for (const c of cars) c.g.position.x = ((c.x0 + c.dirn * c.v * t + 55) % 110 + 110) % 110 - 55; });
  } else {
    const n = spec.place === 'forest' ? 120 : spec.place === 'meadow' ? 26 : spec.place === 'snowfield' ? 16 : 0, clear = spec.place === 'forest' ? 4.6 : 7;
    for (let i = 0; i < n; i++) { const a = R() * 6.283, d = clear + Math.pow(R(), 0.7) * 44, x = Math.cos(a) * d, z = Math.sin(a) * d; if (z > 3 && Math.abs(x) < 2.2 + z * 0.12) continue;   // keep the view from the front open
      tree(x, z, 0.9 + R() * 1.3, spec.place === 'meadow' ? 'round' : R() < 0.8 ? 'pine' : 'round'); }
    for (let i = 0; i < (beach ? 6 : 22); i++) { const a = R() * 6.283, d = 3.2 + R() * 30; rock(Math.cos(a) * d, Math.sin(a) * d, 0.2 + R() * 0.7); }
    if (beach) { const sea = mesh(new THREE.PlaneGeometry(200, 120, 40, 24), new THREE.MeshStandardMaterial({ color: night ? 0x10305a : 0x2f8fc4, roughness: 0.25, metalness: 0.3, flatShading: true }), 0, -0.25, -72, false); sea.rotation.x = -Math.PI / 2; scene.add(sea);
      const p = sea.geometry.attributes.position, z0 = Float32Array.from({ length: p.count }, (_, i) => hash(p.getX(i), p.getY(i)) * 6.28); ticks.push(t => { for (let i = 0; i < p.count; i++) p.setZ(i, Math.sin(t * 1.3 + z0[i]) * 0.22); p.needsUpdate = true; sea.geometry.computeVertexNormals(); }); }
  }

  // ----- props -----
  const props = spec.props || [], propPos = new THREE.Vector3().copy(anchor);
  if (props.includes('campfire')) { const g = new THREE.Group(); g.position.copy(anchor); propPos.set(anchor.x, anchor.y + 0.35, anchor.z);
    for (let i = 0; i < 9; i++) { const a = i / 9 * 6.283, s = mesh(new THREE.DodecahedronGeometry(0.13 + R() * 0.05, 0), mat(0x6f737a), Math.cos(a) * 0.55, 0.07, Math.sin(a) * 0.55); g.add(s); }
    for (let i = 0; i < 4; i++) { const l = mesh(new THREE.CylinderGeometry(0.06, 0.07, 0.8, 5), mat(0x3d2a1c), 0, 0.16, 0); l.rotation.set(Math.PI / 2 - 0.5, i * Math.PI / 2 + 0.4, 0, 'YXZ'); g.add(l); }
    const flames = []; for (let i = 0; i < 5; i++) { const f = mesh(new THREE.ConeGeometry(0.16 - i * 0.02, 0.5 + R() * 0.3, 5), new THREE.MeshBasicMaterial({ color: [0xff5a1f, 0xff8a1f, 0xffc23d, 0xffe08a, 0xff7a2f][i], transparent: true, opacity: 0.92 }), (R() - 0.5) * 0.24, 0.42, (R() - 0.5) * 0.24, false); f.userData.p = R() * 6; flames.push(f); g.add(f); }
    const l = new THREE.PointLight(0xff8a3a, 30, 15, 1.7); l.position.set(0, 0.75, 0); l.castShadow = true; l.shadow.mapSize.set(1024, 1024); l.shadow.bias = -0.004; g.add(l); lights.push({ light: l, base: night ? 30 : 12, flicker: 0.22 });
    { const b = new THREE.PointLight(0xffa45c, night ? 7 : 3, 9, 1.6); b.position.set(0, 1.5, 1.7); g.add(b); lights.push({ light: b, base: night ? 7 : 3, flicker: 0.12 }); }   // warm bounce toward the camera side, so firelit faces are not half black
    const gl = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: 0xff9a4a, transparent: true, opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending })); gl.scale.setScalar(3.4); gl.position.set(0, 0.6, 0); g.add(gl);
    const N = 46, ep = new Float32Array(N * 3), es = Float32Array.from({ length: N * 3 }, () => R()), eg = new THREE.BufferGeometry(); eg.setAttribute('position', new THREE.BufferAttribute(ep, 3));
    g.add(new THREE.Points(eg, new THREE.PointsMaterial({ map: glowTex, color: 0xffb060, size: 0.09, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })));
    ticks.push(t => { for (const f of flames) { const k = 0.75 + 0.45 * vnoise(t * 5 + f.userData.p, f.userData.p); f.scale.set(0.9 + 0.3 * vnoise(t * 7, f.userData.p), k, 0.9); f.position.y = 0.2 + 0.28 * k; f.rotation.z = (vnoise(t * 3, f.userData.p * 2) - 0.5) * 0.5; }
      gl.material.opacity = 0.4 + 0.2 * vnoise(t * 6, 1); for (let i = 0; i < N; i++) { const life = (t * (0.25 + es[i * 3] * 0.3) + es[i * 3 + 1] * 9) % 1; ep[i * 3] = Math.sin(life * 5 + es[i * 3 + 2] * 6.28) * 0.28 * (0.3 + life); ep[i * 3 + 1] = 0.4 + life * 2.6; ep[i * 3 + 2] = Math.cos(life * 4 + es[i * 3] * 6.28) * 0.28 * (0.3 + life); } eg.attributes.position.needsUpdate = true; });
    scene.add(g); }
  if (props.includes('lamp') && !street) lamp(anchor.x - 2.6, anchor.z - 1.6);
  if (props.includes('tent')) { const t = mesh(new THREE.ConeGeometry(1.5, 1.7, 4), mat(0x8f3a1c), anchor.x + 4.8, 0.85, anchor.z - 4.2); t.rotation.y = 0.6; scene.add(t); if (snow) { const c = mesh(new THREE.ConeGeometry(0.8, 0.7, 4), snowM, anchor.x + 4.8, 1.42, anchor.z - 4.2, false); c.rotation.y = 0.6; scene.add(c); } }
  const seatProp = props.includes('bench') ? 'bench' : (props.includes('logs') || props.includes('campfire')) ? 'logs' : null;

  if (spec.puddle) { const pd = mesh(new THREE.CircleGeometry(1.15, 14), new THREE.MeshStandardMaterial({ color: 0x8d9ba6, roughness: 0.12, metalness: 0.25 }), spec.puddle[0], anchor.y + 0.085, spec.puddle[1], false); pd.rotation.x = -Math.PI / 2; pd.scale.y = 0.8; scene.add(pd); }
  // everything built so far is the place itself; it sits in one group so that a walk can slide it past people who stay where they are
  const place = new THREE.Group(); for (const c of [...scene.children]) if (!c.isLight && !(c.material && c.material.fog === false)) place.add(c); scene.add(place);

  // ----- people -----
  const loader = new THREE.TextureLoader(), load = u => new Promise(r => loader.load(u, t => { t.colorSpace = THREE.SRGBColorSpace; r(t); }, undefined, () => r(null)));
  const people = [], np = (spec.people || []).length, spread = np > 1 ? (seatProp === 'logs' && props.includes('campfire') ? 1.45 : 0.72) : 0;
  for (let i = 0; i < np; i++) { const P = spec.people[i], g = new THREE.Group(), sit = P.pose === 'sit', skinM = mat(C(P.skin || '#d08b5b')), shirtM = mat(C(P.shirt || '#c2410c')), pantsM = mat(C(P.pants || '#2b3442')), hairM = mat(C(P.hair || '#2c1b18')), shoeM = mat(0x1e1e22);
    const x = np > 1 ? lerp(-spread, spread, i / (np - 1)) : 0; g.position.set(anchor.x + x, anchor.y, anchor.z + (np > 1 ? Math.abs(x) * 0.12 : 0)); const hipY = sit ? 0.46 : 0.86;
    if (sit) { const s = seatProp === 'bench' ? mesh(new THREE.BoxGeometry(0.9, 0.08, 0.42), mat(0x6b4a32), 0, 0.42, -0.02) : (() => { const l = mesh(new THREE.CylinderGeometry(0.2, 0.2, 1.0, 7), mat(0x4a3424), 0, 0.2, -0.05); l.rotation.z = Math.PI / 2; return l; })(); g.add(s); if (snow && seatProp !== 'bench') { const c = mesh(new THREE.BoxGeometry(0.22, 0.06, 0.3), snowM, 0.42, 0.4, -0.05, false); g.add(c); } }
    const body = new THREE.Group(); body.position.y = hipY; g.add(body);
    const torso = mesh(new THREE.CylinderGeometry(0.19, 0.24, 0.58, 7), shirtM, 0, 0.3, 0); torso.scale.z = 0.72; body.add(torso); body.add(mesh(new THREE.CylinderGeometry(0.07, 0.08, 0.1, 6), skinM, 0, 0.63, 0));
    if (P.scarf || snow) { const s = mesh(new THREE.TorusGeometry(0.115, 0.055, 5, 8), mat(C(P.scarf || '#e3b23c')), 0, 0.61, 0); s.rotation.x = Math.PI / 2; body.add(s); }
    const head = new THREE.Group(); head.position.y = 0.86; body.add(head); const hr = 0.2;
    const skull = mesh(new THREE.SphereGeometry(hr, 18, 14), new THREE.MeshStandardMaterial({ color: skinM.color, roughness: 0.85 })); skull.scale.set(1, 1.08, 0.98); head.add(skull);
    for (const sx of [-1, 1]) head.add(mesh(new THREE.SphereGeometry(0.045, 5, 4), skinM, sx * hr * 0.98, -0.01, 0));
    const hs = P.hairStyle || 'short';                                                  // hair on the skull
    if (hs !== 'bald') { const cap = mesh(new THREE.SphereGeometry(hr * 1.06, 10, 6, 0, Math.PI * 2, 0, hs === 'beanie' ? 1.25 : 1.12), hs === 'beanie' ? mat(C(P.hat || '#2f6f8f')) : hairM, 0, 0.012, -0.012); cap.scale.set(1.01, 1.1, 1.02); cap.rotation.x = -0.28; head.add(cap);
      if (hs === 'bun') head.add(mesh(new THREE.IcosahedronGeometry(0.085, 0), hairM, 0, 0.26, -0.05));
      if (hs === 'long') { const b = mesh(new THREE.CylinderGeometry(0.215, 0.19, 0.44, 9, 1, true, Math.PI / 2 - 0.25, Math.PI + 0.5), new THREE.MeshStandardMaterial({ color: hairM.color, flatShading: true, roughness: 0.9, side: THREE.DoubleSide }), 0, -0.15, -0.01); head.add(b); }
      if (hs === 'curly') for (let k = 0; k < 9; k++) { const a = k / 9 * 6.283; head.add(mesh(new THREE.IcosahedronGeometry(0.075, 0), hairM, Math.cos(a) * 0.14, 0.17 + (k % 2) * 0.03, Math.sin(a) * 0.13 - 0.03)); }
      if (hs === 'beanie') head.add(mesh(new THREE.IcosahedronGeometry(0.05, 0), mat(0xf4f4f4), 0, 0.235, -0.07)); }
    const faces = {}; await Promise.all(Object.entries(P.faces || {}).map(async ([k, u]) => { faces[k] = await load(u); }));
    const fm = new THREE.MeshStandardMaterial({ map: Object.values(faces)[0] || null, transparent: true, roughness: 0.9, polygonOffset: true, polygonOffsetFactor: -4, depthWrite: false });
    const fg = new THREE.SphereGeometry(hr * 1.012, 18, 12, Math.PI / 2 - 0.92, 1.84, Math.PI / 2 - 0.78, 1.5); const face = new THREE.Mesh(fg, fm); face.scale.copy(skull.scale); if (Object.keys(faces).length) head.add(face);
    const limb = (len, r, m) => { const pv = new THREE.Group(), seg = mesh(new THREE.CylinderGeometry(r, r * 0.86, len, 6), m, 0, -len / 2, 0); pv.add(seg); return pv; };
    const arms = [], legs = [];
    for (const sx of [-1, 1]) { const up = limb(0.3, 0.062, shirtM); up.position.set(sx * 0.25, 0.53, 0); const fo = limb(0.27, 0.052, shirtM); fo.position.y = -0.3; up.add(fo); fo.add(mesh(new THREE.IcosahedronGeometry(0.058, 0), skinM, 0, -0.3, 0)); body.add(up); arms.push({ up, fo, sx });
      const th = limb(0.42, 0.085, pantsM); th.position.set(sx * 0.11, 0.0, 0); const sh = limb(0.4, 0.07, pantsM); sh.position.y = -0.42; th.add(sh); sh.add(mesh(new THREE.BoxGeometry(0.11, 0.07, 0.24), shoeM, 0, -0.42, 0.06)); body.add(th); legs.push({ th, sh, sx });
      if (sit) { th.rotation.x = -1.45; th.rotation.z = sx * 0.08; sh.rotation.x = 1.35; } }
    if (P.umbrella) { const u = new THREE.Group(); u.add(mesh(new THREE.CylinderGeometry(0.012, 0.012, 1.1, 5), mat(0x222222), 0, 0.5, 0), mesh(new THREE.ConeGeometry(0.75, 0.26, 8), mat(C(P.umbrella === true ? '#c2410c' : P.umbrella)), 0, 1.1, 0)); u.position.set(0.3, 0.3, 0.16); body.add(u); P._umb = true; }
    scene.add(g); people.push({ P, g, body, head, torso, arms, legs, fm, faces, sit, hipY, phase: R() * 6.28, id: P.id }); }
  for (const p of people) { const o = people.find(q => q !== p); p.yaw = o ? Math.atan2(o.g.position.x - p.g.position.x, (o.g.position.z + (props.includes('campfire') ? 0 : 0.0)) - p.g.position.z) * (spec.walk ? 0.12 : props.includes('campfire') ? 0.42 : 0.5) : 0; p.g.rotation.y = p.yaw; }
  const headPos = p => p.head.getWorldPosition(new THREE.Vector3()); scene.updateMatrixWorld(true);

  // ----- passers-by on a street -----
  if (street) { const cols = [0x9b2c2c, 0x2c5282, 0x276749, 0x744210, 0x553c9a, 0x2d3748, 0xb7791f];
    for (let i = 0; i < (spec.extras ?? 6) + 2; i++) { const g = new THREE.Group(), sM = mat(cols[Math.floor(R() * cols.length)]), kM = mat([0xf0c8a0, 0xd08b5b, 0xae5d29, 0x8d5524][Math.floor(R() * 4)]), dirn = R() < 0.5 ? 1 : -1;
      const t = mesh(new THREE.CylinderGeometry(0.18, 0.23, 0.58, 6), sM, 0, 1.16, 0); t.scale.z = 0.7; g.add(t, mesh(new THREE.SphereGeometry(0.19, 7, 6), kM, 0, 1.68, 0)); const L = [];
      for (const sx of [-1, 1]) { const pv = new THREE.Group(); pv.position.set(sx * 0.1, 0.86, 0); pv.add(mesh(new THREE.CylinderGeometry(0.08, 0.065, 0.84, 5), mat(0x2b3442), 0, -0.42, 0)); g.add(pv); L.push(pv); }
      if (wet) g.add(mesh(new THREE.CylinderGeometry(0.012, 0.012, 1.0, 4), mat(0x222222), 0.22, 1.7, 0.1), mesh(new THREE.ConeGeometry(0.7, 0.24, 8), mat(cols[Math.floor(R() * cols.length)]), 0.22, 2.25, 0.1));
      const z = (R() < 0.5 ? -1 : 1) * (4.4 + R() * 2.4), x0 = (R() - 0.5) * 60, v = 1.0 + R() * 0.7; g.rotation.y = dirn > 0 ? Math.PI / 2 : -Math.PI / 2; g.position.set(0, 0.16, z); scene.add(g);
      if (Math.abs(z - anchor.z) < 0.9) g.position.z = z - 1.6;
      ticks.push(t => { g.position.x = ((x0 + dirn * v * t + 30) % 60 + 60) % 60 - 30; const s = Math.sin(t * v * 5.2 + x0); L[0].rotation.x = s * 0.5; L[1].rotation.x = -s * 0.5; g.position.y = 0.16 + Math.abs(Math.cos(t * v * 5.2 + x0)) * 0.03; }); } }

  // ----- weather -----
  const wind = spec.wind ?? (spec.weather === 'storm' ? 1 : spec.weather === 'snow' ? 0.35 : 0.2), box = { x: 34, y: 16, z: 34 };
  if (snow && spec.weather === 'snow') { const N = 3200, p = new Float32Array(N * 3), s = Float32Array.from({ length: N * 4 }, () => R()), g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    const pts = new THREE.Points(g, new THREE.PointsMaterial({ map: glowTex, color: 0xffffff, size: 0.13, transparent: true, opacity: 0.95, depthWrite: false })); pts.frustumCulled = false; scene.add(pts);
    ticks.push((t, f, cam) => { for (let i = 0; i < N; i++) { const v = 0.7 + s[i * 4 + 3] * 0.8; p[i * 3] = cam.x + ((s[i * 4] * box.x + wind * t * 1.2 + Math.sin(t * 0.9 + s[i * 4 + 1] * 20) * 0.5) % box.x + box.x) % box.x - box.x / 2; p[i * 3 + 1] = ((s[i * 4 + 1] * box.y - v * t) % box.y + box.y) % box.y - 0.5; p[i * 3 + 2] = cam.z + (s[i * 4 + 2] * box.z + Math.cos(t * 0.7 + s[i * 4] * 20) * 0.4) % box.z - box.z / 2; } g.attributes.position.needsUpdate = true; }); }
  if (wet) { const N = spec.weather === 'storm' ? 5200 : 3400, p = new Float32Array(N * 6), s = Float32Array.from({ length: N * 4 }, () => R()), g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
    const ln = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: night ? 0x9fb4d8 : 0xdbe6f2, transparent: true, opacity: 0.5 })); ln.frustumCulled = false; scene.add(ln); const lean = wind * 0.32;
    ticks.push((t, f, cam) => { for (let i = 0; i < N; i++) { const v = 13 + s[i * 4 + 3] * 5, y = ((s[i * 4 + 1] * box.y - v * t) % box.y + box.y) % box.y, x = cam.x + ((s[i * 4] * box.x + lean * (box.y - y)) % box.x) - box.x / 2, z = cam.z + s[i * 4 + 2] * box.z - box.z / 2; p.set([x, y, z, x - lean * 0.55, y + 0.55, z], i * 6); } g.attributes.position.needsUpdate = true; });
    if (spec.weather === 'storm') { const fl = new THREE.DirectionalLight(0xcfe0ff, 0); fl.position.set(10, 30, -20); scene.add(fl); const base = amb.intensity, bg0 = scene.background.clone();
      ticks.push(t => { const k = Math.floor(t / 2.6), tt = t - k * 2.6 - hash(k, 9) * 1.6, a = tt > 0 && tt < 0.5 ? Math.max(0, Math.sin(tt * 40)) * Math.exp(-tt * 7) : 0; fl.intensity = a * 7; amb.intensity = base + a * 2.2; scene.background.copy(bg0).lerp(C(0x9fb0d0), a * 0.7); scene.fog.color.copy(scene.background); }); } }

  // ----- camera -----
  const cam = new THREE.PerspectiveCamera(W > H ? 34 : 46, W / H, 0.1, 400), kA = W > H ? 1 : 1.55, mid = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  if (people.length) { for (const p of people) mid.add(headPos(p)); mid.multiplyScalar(1 / people.length); } else mid.copy(anchor).setY(anchor.y + 1.2);
  const shot = spec.shot || { cam: 'wide' }, [kind, who] = String(shot.cam || 'wide').split(':'), subj = people.find(p => p.id === who) || people[0], other = people.find(p => p !== subj);
  const frontZ = 1;                                                    // the open side of every place is +z
  function camera(u) { const e = sm(u), V = (x, y, z) => new THREE.Vector3(x, y, z); let pos, look;
    if (kind === 'two') { pos = V(mid.x + lerp(-0.5, 0.5, e), mid.y + 0.25, mid.z + 4.3 * kA * frontZ - e * 0.4); look = V(mid.x, mid.y - 0.12, mid.z); }
    else if (kind === 'close' && subj) { const h = headPos(subj), side = other ? Math.sign(other.g.position.x - subj.g.position.x) || 1 : 1; pos = V(h.x + side * lerp(0.75, 0.6, e), h.y + 0.06, h.z + lerp(1.95, 1.7, e) * (W > H ? 1 : 1.12)); look = V(h.x, h.y - 0.03, h.z); }
    else if (kind === 'over' && subj && other) { const a = headPos(other), b = headPos(subj), d = b.clone().sub(a).setY(0).normalize(), s = V(-d.z, 0, d.x); pos = a.clone().addScaledVector(d, -1.05).addScaledVector(s, 0.42 * (s.z > 0 ? 1 : -1)).add(V(0, 0.3, 0.9)); look = b.clone().add(V(0, -0.05, 0)); pos.x += lerp(-0.08, 0.08, e); }
    else if (kind === 'full') { pos = V(mid.x + lerp(-0.35, 0.35, e), anchor.y + 1.05, mid.z + (W > H ? 4.4 : 5.4) - e * 0.3); look = V(mid.x, anchor.y + 0.95, mid.z); }                 // both people head to toe
    else if (kind === 'fallen' && subj) { const h = headPos(subj); pos = V(h.x, h.y + lerp(4.6, 4.1, e) * (W > H ? 0.8 : 1), h.z + 1.75); look = V(h.x, h.y, h.z + 0.8); }       // looking down at someone on the ground
    else if (kind === 'orbit') { const a = lerp(-0.55, 0.55, e) + (shot.angle || 0), r = 7.2 * kA; pos = V(mid.x + Math.sin(a) * r, mid.y + 1.4, mid.z + Math.cos(a) * r); look = V(mid.x, mid.y - 0.3, mid.z); }
    else if (kind === 'crane') { pos = V(mid.x + lerp(-1.2, 0.8, e), lerp(mid.y - 0.3, mid.y + 5.5, e), mid.z + lerp(4.6, 12, e) * kA); look = V(mid.x, mid.y - 0.3, mid.z); }
    else if (kind === 'low') { pos = V(mid.x + lerp(2.6, 2.0, e), anchor.y + 0.35, mid.z + 4.4 * kA); look = V(mid.x, mid.y + 0.1, mid.z); }
    else if (kind === 'top') { pos = V(mid.x + lerp(-0.6, 0.6, e), mid.y + 9, mid.z + 5.5); look = V(mid.x, mid.y - 1, mid.z); }
    else if (kind === 'prop') { pos = V(propPos.x + lerp(-0.5, 0.5, e), propPos.y + 0.55, propPos.z + lerp(2.6, 2.1, e)); look = V(propPos.x, propPos.y + 0.15, propPos.z); }
    else { pos = V(mid.x + lerp(-0.7, 0.7, e), mid.y + 1.5, mid.z + lerp(10.5, 9.2, e) * kA); look = V(mid.x, mid.y + (W > H ? -0.2 : 0.3), mid.z); }        // wide
    cam.position.copy(pos); cam.up.copy(up); cam.lookAt(look); }

  // ----- per-frame -----
  const walk = spec.walk || 0, dist0 = spec.dist0 || 0, fall = spec.fall, faller = fall && people.find(p => p.id === fall.id), anyDown = people.some(p => p.P.state === 'down'); let splash = null;
  if (faller) { const N = 70, pp = new Float32Array(N * 3), sv = Float32Array.from({ length: N * 3 }, () => R()), g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pp, 3));
    const pts = new THREE.Points(g, new THREE.PointsMaterial({ map: glowTex, color: 0xcfe6f5, size: 0.17, transparent: true, depthWrite: false })); pts.frustumCulled = false; pts.visible = false; scene.add(pts);
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.5, 0.63, 20), new THREE.MeshBasicMaterial({ color: 0xdfeef8, transparent: true, side: THREE.DoubleSide, depthWrite: false })); ring.rotation.x = -Math.PI / 2; ring.visible = false; scene.add(ring);
    splash = u => { const on = u > 0.42 && u < 2.0, v = u - 0.42, c = faller.g.position; pts.visible = ring.visible = on; if (!on) return;
      for (let i = 0; i < N; i++) { const a = sv[i * 3] * 6.283, s_ = 0.8 + sv[i * 3 + 1] * 2.2, vy = 2.2 + sv[i * 3 + 2] * 2.6, y = vy * v - 4.9 * v * v; pp[i * 3] = c.x + Math.cos(a) * s_ * v; pp[i * 3 + 1] = y > 0 ? c.y + y + 0.1 : -5; pp[i * 3 + 2] = c.z - 0.45 + Math.sin(a) * s_ * v * 0.7; } g.attributes.position.needsUpdate = true;
      ring.position.set(c.x, c.y + 0.1, c.z - 0.45); ring.scale.setScalar(1 + v * 2.4); ring.material.opacity = Math.max(0, 0.8 - v * 0.9); }; }
  const fps = spec.fps || 30, dur = shot.dur || 4, t0 = spec.t0 || 0, sp = spec.speak, speaker = sp && people.find(p => p.id === sp.id), env = sp ? sp.env || [] : [];
  function seek(t) { const gt = t0 + t, f = Math.round(t * fps), fi = sp ? f - Math.round((sp.at || 0) * fps) : -1, on = fi >= 0 && fi < env.length, lv = on ? env[fi] : 0;
    let lvS = 0; if (sp) { let n = 0; for (let k = -4; k <= 4; k++) { const j = fi + k; if (j >= 0 && j < env.length) { lvS += env[j]; n++; } } lvS = n ? lvS / n : 0; }
    const tf = fall ? fall.at : 1e9, tw = Math.max(0, Math.min(t, tf + 0.12)), dist = dist0 + walk * tw, moving = walk > 0 && t < tf + 0.12; place.position.z = -dist;
    for (const L of lights) L.light.intensity = L.base * (1 - L.flicker + L.flicker * 2 * vnoise(gt * 9, L.base));
    for (const p of people) { const talk = p === speaker && on, br = Math.sin(gt * 1.6 + p.phase), M = p.P.mouths || [], E = p.P.eyes || [];
      const mouth = talk ? (lv < 0.14 ? M[0] : lv < 0.6 ? M[1] : M[2]) : M[0], blink = (Math.floor(gt * fps) + Math.floor(p.phase * 40)) % 96 < 4, eyes = blink ? E[1] : (talk || !speaker ? E[0] : E[2]), tx = p.faces[mouth + '|' + eyes]; if (tx && p.fm.map !== tx) { p.fm.map = tx; p.fm.needsUpdate = true; }
      p.torso.scale.y = 1 + br * 0.012; p.body.rotation.z = Math.sin(gt * 0.7 + p.phase) * 0.012; p.body.rotation.x = p.sit ? 0.12 : 0;
      const look = speaker && p !== speaker ? Math.atan2(speaker.g.position.x - p.g.position.x, speaker.g.position.z - p.g.position.z) - p.yaw : (p === speaker && other && people.length > 1 ? 0.0 : 0);
      p.head.rotation.y = Math.max(-0.7, Math.min(0.7, look * 0.55)) + Math.sin(gt * 0.5 + p.phase) * 0.04; p.head.rotation.x = (talk ? Math.sin(gt * 6.3) * 0.035 * (0.4 + lvS) - 0.02 : Math.sin(gt * 0.9 + p.phase) * 0.02) + (p.sit ? -0.1 : 0); p.head.rotation.z = talk ? Math.sin(gt * 2.1) * 0.03 : 0;
      for (const a of p.arms) { const g = p === speaker ? sm(lvS * 1.6) * (on ? 1 : 0) : 0, w = Math.sin(gt * 3.1 + a.sx) * 0.12 * g;
        if (p.P._umb && a.sx > 0) { a.up.rotation.set(-0.5, 0, 0); a.fo.rotation.set(-1.6, 0, 0); continue; }
        if (p.sit) { a.up.rotation.set(-0.55 - g * 0.25 * (a.sx > 0 ? 1 : 0.3), 0, a.sx * 0.12); a.fo.rotation.set(-0.75 - g * 0.7 * (a.sx > 0 ? 1 : 0.2) + w, 0, -a.sx * 0.25); }
        else { a.up.rotation.set(-0.08 - g * 0.35 * (a.sx > 0 ? 1 : 0.4) + br * 0.01, 0, a.sx * 0.1); a.fo.rotation.set(-0.18 - g * 1.15 * (a.sx > 0 ? 1 : 0.4) + w, 0, 0); } }
      const down = p.P.state === 'down' || (p === faller && t >= tf), u = p.P.state === 'down' ? 9 : t - tf;                       // walking, slipping, lying on the ground
      if (!p.sit) { p.body.position.set(0, p.hipY, 0); for (const l of p.legs) { l.th.rotation.set(0, 0, 0); l.sh.rotation.x = 0; } }
      if (moving && !down && !p.sit) { const ph = dist * 4.4 + p.phase; p.body.position.y = p.hipY + Math.abs(Math.cos(ph)) * 0.035; p.body.rotation.x = 0.05;
        for (const l of p.legs) { const s = Math.sin(ph + (l.sx > 0 ? 0 : Math.PI)); l.th.rotation.x = -s * 0.5; l.sh.rotation.x = Math.max(0, -s) * 0.75 + 0.05; }
        for (const a of p.arms) { if (p.P._umb && a.sx > 0) continue; a.up.rotation.x += -Math.sin(ph + (a.sx > 0 ? Math.PI : 0)) * 0.4; a.fo.rotation.x += -0.2; } }
      if (down) { const k1 = sm(u / 0.22), k2 = sm((u - 0.18) / 0.42), bn = u > 0.6 && u < 2 ? Math.exp(-(u - 0.6) * 6) * Math.sin((u - 0.6) * 18) * 0.06 : 0;
        p.body.rotation.x = -(0.35 * k1 + 1.2 * k2); p.body.position.set(0, lerp(p.hipY, 0.26, k2) + k1 * (1 - k2) * 0.14 + bn, -0.3 * k2);
        for (const l of p.legs) { l.th.rotation.x = l.sx > 0 ? -1.5 * k1 + 0.75 * k2 : -0.35 * k1 - 0.1 * k2; l.sh.rotation.x = l.sx > 0 ? 0.15 + 0.5 * k2 : 0.2; }
        for (const a of p.arms) { a.up.rotation.set(-2.5 * k1 + 1.1 * k2, 0, a.sx * (0.5 * k1 + 0.55 * k2)); a.fo.rotation.set(-0.3, 0, 0); }
        if (u < 1.0 && p.faces[M[2] + '|' + E[0]]) { p.fm.map = p.faces[M[2] + '|' + E[0]]; p.fm.needsUpdate = true; }
        p.head.rotation.set(0.12 * k2 + (talk ? Math.sin(gt * 6.3) * 0.03 : 0), 0, 0); }
      else if ((faller && p !== faller && t >= tf) || (anyDown && p.P.state !== 'down')) { const k = anyDown ? 1 : sm((t - tf - 0.35) / 0.4); p.head.rotation.x += 0.3 * k; p.body.rotation.x += 0.08 * k; } }   // the other one looks down at them
    if (splash) splash(t - tf);
    scene.updateMatrixWorld(true); camera(Math.min(t / dur, 1));
    for (const fn of ticks) fn(gt, f, cam.position);
    renderer.render(scene, cam); }
  seek(0); return { seek, scene, cam, renderer };
}
