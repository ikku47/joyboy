// joyboy site save: download a public web page so a video can work with its parts.
//   node site_save.mjs <url> <outDir> [desktop|mobile]
// Writes into <outDir>:
//   page.png        the whole page as one sharp image
//   page.mhtml      the page itself with its styles and images, as the browser saved it (opens offline in Chrome)
//   elements.json   every notable element (headings, text, buttons, links, images, sections, inputs ...) with its
//                   words and its position on the page, plus the page's title, colours and fonts
// Only public pages. Nothing is typed, clicked or submitted, and pages behind a login are not for this.
import puppeteer from 'puppeteer-core';
import fs from 'node:fs'; import path from 'node:path';
const [url, out, device = 'desktop'] = process.argv.slice(2);
if (!url || !out) { console.error('usage: node site_save.mjs <url> <outDir> [desktop|mobile]'); process.exit(1); }
const chrome = process.env.CHROME_PATH || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => fs.existsSync(p));
if (!chrome) { console.error('no Chrome-family browser found; set CHROME_PATH'); process.exit(2); }
fs.mkdirSync(out, { recursive: true });
const mobile = device === 'mobile', vw = mobile ? 390 : 1440, vh = mobile ? 844 : 900, scale = mobile ? 3 : 1.5, maxH = mobile ? 7000 : 6500;
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--hide-scrollbars'] });
const page = await browser.newPage();
await page.setViewport({ width: vw, height: vh, deviceScaleFactor: scale, isMobile: mobile, hasTouch: mobile });
await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
try { await page.goto(url, { waitUntil: 'networkidle2', timeout: 45000 }); } catch (e) { console.error('load warning:', e.message); }
await page.addStyleTag({ content: '*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important;caret-color:transparent!important}' });
await page.evaluate(async () => { const h = document.documentElement.scrollHeight; for (let y = 0; y < h; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } window.scrollTo(0, 0); await new Promise(r => setTimeout(r, 500)); });
const info = await page.evaluate((maxH) => {
  const H = Math.min(document.documentElement.scrollHeight, maxH), W = document.documentElement.clientWidth, cs = e => getComputedStyle(e);
  const sel = e => { const p = []; while (e && e.nodeType === 1 && e !== document.body && p.length < 6) { if (e.id) { p.unshift('#' + CSS.escape(e.id)); break; }
    const t = e.tagName.toLowerCase(), sib = e.parentElement ? [...e.parentElement.children].filter(c => c.tagName === e.tagName) : []; p.unshift(sib.length > 1 ? `${t}:nth-of-type(${sib.indexOf(e) + 1})` : t); e = e.parentElement; } return p.join(' > '); };
  const kindOf = e => { const t = e.tagName.toLowerCase(), c = (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className || '').toString().toLowerCase();
    if (/^h[1-4]$/.test(t)) return 'heading'; if (t === 'img' || t === 'video' || t === 'picture' || t === 'canvas' || t === 'svg' || t === 'figure') return 'image';
    if (t === 'button' || (t === 'a' && /btn|button|cta/.test(c)) || e.getAttribute('role') === 'button') return 'button'; if (t === 'a') return 'link';
    if (t === 'input' || t === 'textarea' || t === 'select' || t === 'form') return 'input'; if (t === 'nav' || t === 'header') return 'nav'; if (t === 'footer') return 'footer';
    if (t === 'section' || t === 'article' || t === 'main') return 'section'; if (/card|feature|tile|plan|price|testimonial|item/.test(c)) return 'card'; if (t === 'pre' || t === 'code' || t === 'table') return 'block'; return 'text'; };
  const seen = new Set(), list = [];
  for (const e of document.querySelectorAll('h1,h2,h3,h4,p,a,button,img,video,canvas,figure,section,article,header,footer,nav,form,input,textarea,li,blockquote,pre,table,[role="button"],[class*="card"],[class*="feature"],[class*="hero"],[class*="price"],[class*="plan"],[class*="testimonial"]')) {
    const r = e.getBoundingClientRect(), st = cs(e), x = r.left + scrollX, y = r.top + scrollY;
    if (r.width < 24 || r.height < 14 || y >= H || x >= W || st.visibility === 'hidden' || st.display === 'none' || +st.opacity < 0.1) continue;
    const kind = kindOf(e), text = (e.innerText || e.alt || e.getAttribute('aria-label') || e.placeholder || '').replace(/\s+/g, ' ').trim();
    if (kind === 'text' && text.length < 28) continue; if (kind === 'link' && (!text || r.height < 20)) continue; if (kind === 'image' && r.width * r.height < 6000) continue;
    const key = [Math.round(x / 4), Math.round(y / 4), Math.round(r.width / 4), Math.round(r.height / 4)].join(','); if (seen.has(key)) continue; seen.add(key);
    list.push({ kind, tag: e.tagName.toLowerCase(), text: text.slice(0, 110), selector: sel(e), rect: { x: Math.round(x), y: Math.round(y), w: Math.round(Math.min(r.width, W - x)), h: Math.round(Math.min(r.height, H - y)) }, size: parseFloat(st.fontSize) || 0 });
  }
  list.sort((a, b) => a.rect.y - b.rect.y || a.rect.x - b.rect.x); const els = list.slice(0, 260).map((e, i) => ({ id: i, ...e }));
  const b = cs(document.body), h1 = document.querySelector('h1'), btn = document.querySelector('button, a[class*="btn"], a[class*="button"], [role="button"]');
  const fonts = [...new Set([b.fontFamily, h1 ? cs(h1).fontFamily : null].filter(Boolean).map(f => f.split(',')[0].replace(/["']/g, '').trim()))];
  const bg = [document.documentElement, document.body].map(e => cs(e).backgroundColor).find(c => c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c)) || 'rgb(255, 255, 255)';
  return { title: document.title, description: (document.querySelector('meta[name="description"]') || {}).content || '', lang: document.documentElement.lang || '', width: W, height: H,
    colors: { background: bg, text: b.color, heading: h1 ? cs(h1).color : b.color, button: btn ? cs(btn).backgroundColor : null, buttonText: btn ? cs(btn).color : null }, fonts, elements: els };
}, maxH);
await page.screenshot({ path: path.join(out, 'page.png'), clip: { x: 0, y: 0, width: info.width, height: info.height } });
try { const cdp = await page.createCDPSession(); const { data } = await cdp.send('Page.captureSnapshot', { format: 'mhtml' }); fs.writeFileSync(path.join(out, 'page.mhtml'), data); } catch (e) { console.error('could not save page.mhtml:', e.message); }
fs.writeFileSync(path.join(out, 'elements.json'), JSON.stringify({ url, device, scale, saved: new Date().toISOString(), ...info }, null, 1));
await browser.close();
console.log(`saved ${url} -> ${out}: ${info.width}x${info.height} css px, ${info.elements.length} elements`);
