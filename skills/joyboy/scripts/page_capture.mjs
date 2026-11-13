// joyboy page capture: a full-length screenshot of a real web page, for website tours and app showcases.
//   node page_capture.mjs <url> <out.png> [mobile|desktop]
// mobile = 390 px wide phone layout at 2x; desktop = 1440 px wide. Only public pages; nothing is typed or clicked.
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
const [url, out, device = 'mobile'] = process.argv.slice(2);
const chrome = process.env.CHROME_PATH || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => fs.existsSync(p));
if (!chrome) { console.error('no Chrome-family browser found; set CHROME_PATH'); process.exit(2); }
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--hide-scrollbars'] });
const page = await browser.newPage();
await page.setViewport(device === 'mobile' ? { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true } : { width: 1440, height: 900, deviceScaleFactor: 1 });
await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
try { await page.goto(url, { waitUntil: 'networkidle2', timeout: 45000 }); } catch (e) { console.error('load warning:', e.message); }
await page.evaluate(async () => { const h = document.documentElement.scrollHeight; for (let y = 0; y < h; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } window.scrollTo(0, 0); await new Promise(r => setTimeout(r, 400)); });
const full = await page.evaluate(() => document.documentElement.scrollHeight);
await page.screenshot({ path: out, clip: { x: 0, y: 0, width: device === 'mobile' ? 390 : 1440, height: Math.min(full, device === 'mobile' ? 7000 : 9000) } });
await browser.close(); console.log('captured', url, '->', out);
