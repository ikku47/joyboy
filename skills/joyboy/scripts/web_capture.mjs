// joyboy web capture: render an HTML animation (GSAP or anything seekable) to MP4, frame by frame.
//   node web_capture.mjs <page.html> <out.mp4> <width> <height> <fps> <seconds>
// The page must expose a paused GSAP timeline as window.tl, or window.joyboy = { seek(seconds) }.
// Each frame the timeline is moved to an exact time and a screenshot is taken, so the result is
// deterministic and never drops frames, however heavy the animation is.
import puppeteer from 'puppeteer-core';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
const [html, out, W, H, fps, dur, clock] = process.argv.slice(2);   // clock = 'virtual' for pages that animate by themselves
const chrome = process.env.CHROME_PATH || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => fs.existsSync(p));
if (!chrome) { console.error('no Chrome-family browser found; set CHROME_PATH'); process.exit(2); }
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars', '--force-color-profile=srgb', '--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', ...(process.platform === 'darwin' ? ['--use-angle=metal'] : []), `--window-size=${W},${H}`] });
const page = await browser.newPage();
await page.setViewport({ width: +W, height: +H, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
page.on('console', m => { if (m.type() === 'error') console.error('console error:', m.text()); });
await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
if (clock === 'virtual') {
  // Virtual clock: the page's own time (requestAnimationFrame, performance.now, Date.now) is replaced by one we control,
  // so anything that animates by itself (a GSS 3D scene, WebGL, canvas, Lottie, Motion) advances exactly one video frame per step.
  await page.evaluateOnNewDocument(() => {
    let vt = 0, id = 0; const q = new Map(), d0 = Date.now();
    window.requestAnimationFrame = cb => { q.set(++id, cb); return id; };
    window.cancelAnimationFrame = i => { q.delete(i); };
    performance.now = () => vt; Date.now = () => d0 + vt;
    window.__joyboyStep = t => { vt = t * 1000; const cbs = [...q.values()]; q.clear(); for (const cb of cbs) { try { cb(vt); } catch (e) { console.error(e); } } return q.size; };
  });
}
await page.goto('file://' + html);
await page.evaluate(() => document.fonts.ready);
let ready = false;
for (let i = 0; i < 150 && !ready; i++) { ready = await page.evaluate(v => v ? window.joyboyReady === true : !!(window.tl || window.joyboy), clock === 'virtual'); if (!ready) await new Promise(r => setTimeout(r, 100)); }
if (!ready) { console.error(clock === 'virtual' ? 'the page never set window.joyboyReady = true' : 'the page never set window.tl (a paused GSAP timeline) or window.joyboy = { seek(t) }'); await browser.close(); process.exit(3); }
if (clock === 'virtual') for (let i = 0; i < 12; i++) { await page.evaluate(() => window.__joyboyStep(0)); await new Promise(r => setTimeout(r, 120)); }   // let shaders compile and the first frames settle
const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', fps, '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', fps, out], { stdio: ['pipe', 'inherit', 'inherit'] });
const n = Math.round(+fps * +dur);
for (let i = 0; i < n; i++) {
  await page.evaluate((t, v) => { if (v) { if (window.joyboy) window.joyboy.seek(t); window.__joyboyStep(t); } else if (window.joyboy) window.joyboy.seek(t); else window.tl.time(t, false); }, i / +fps, clock === 'virtual');
  const buf = await page.screenshot({ type: 'jpeg', quality: 96 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('captured', n, 'frames ->', out);
