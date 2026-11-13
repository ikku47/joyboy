// joyboy world still: one frame of a world page, for checking a shot before a full capture.
//   node world_still.mjs <page.html> <out.png> <width> <height> <seconds>
import puppeteer from 'puppeteer-core'; import fs from 'node:fs';
const [html, out, W, H, t = '0'] = process.argv.slice(2);
const chrome = process.env.CHROME_PATH || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => fs.existsSync(p));
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars', '--force-color-profile=srgb', '--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', ...(process.platform === 'darwin' ? ['--use-angle=metal'] : []), `--window-size=${W},${H}`] });
const page = await browser.newPage(); await page.setViewport({ width: +W, height: +H, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message)); page.on('console', m => { if (m.type() === 'error') console.error('console error:', m.text()); });
await page.goto('file://' + html);
for (let i = 0; i < 150; i++) { if (await page.evaluate(() => !!window.joyboy)) break; await new Promise(r => setTimeout(r, 100)); }
const t0 = Date.now(); await page.evaluate(t => window.joyboy.seek(t), +t); await page.screenshot({ path: out }); console.log('still', out, (Date.now() - t0) + 'ms');
await browser.close();
