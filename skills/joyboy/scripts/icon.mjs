// joyboy icons: find and render icons from react-icons (Lucide, Font Awesome, Material, Tabler, Heroicons, Phosphor,
// Simple Icons brand logos and more - about 30 sets) instead of drawing SVG by hand.
//   node icon.mjs search <word> [set]          list icon names containing the word (set = lu, fa, fa6, md, tb, hi2, pi, si ...)
//   node icon.mjs render <outDir> <Name> ...   write <Name>.svg and a 512 px transparent <Name>.png for each icon
// A name may be given as "set/Name" when two sets share it (for example fa6/FaRocket).
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const req = createRequire(import.meta.url);
const React = req('react'); const { renderToStaticMarkup } = req('react-dom/server');
const root = path.join(path.dirname(new URL(import.meta.url).pathname), 'node_modules', 'react-icons');
const sets = fs.readdirSync(root).filter(d => d !== 'lib' && fs.existsSync(path.join(root, d, 'index.js')));
const [cmd, ...rest] = process.argv.slice(2);
function find(full) {
  const [a, b] = full.includes('/') ? full.split('/') : [null, full];
  const guess = (b.match(/^[A-Z][a-z]*\d*/) || [''])[0].toLowerCase();
  for (const s of a ? [a] : [guess, ...sets]) { if (!sets.includes(s)) continue; const m = req(`react-icons/${s}`); if (m[b]) return [b, m[b]]; }
  return [b, null];
}
if (cmd === 'search') {
  const q = (rest[0] || '').toLowerCase(), only = rest[1]; const out = [];
  for (const s of sets) { if (only && s !== only) continue; for (const k of Object.keys(req(`react-icons/${s}`))) if (k.toLowerCase().includes(q)) out.push(`${s}/${k}`); }
  console.log(out.slice(0, 150).join('  ')); console.log(`${out.length} matches` + (out.length > 150 ? ' (showing 150; add a set to narrow)' : ''));
} else if (cmd === 'render') {
  const dir = rest[0]; fs.mkdirSync(dir, { recursive: true }); const todo = [];
  for (const full of rest.slice(1)) {
    const [name, Icon] = find(full);
    if (!Icon) { console.error('icon not found: ' + full + '  (try: node icon.mjs search <word>)'); process.exitCode = 1; continue; }
    const svg = renderToStaticMarkup(React.createElement(Icon, { size: 512, color: '#ffffff' }));
    fs.writeFileSync(path.join(dir, name + '.svg'), svg); todo.push([name, svg]);
  }
  if (todo.length) {
    const puppeteer = (await import('puppeteer-core')).default;
    const chrome = process.env.CHROME_PATH || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => fs.existsSync(p));
    if (!chrome) { console.error('no Chrome-family browser found; set CHROME_PATH'); process.exit(2); }
    const browser = await puppeteer.launch({ executablePath: chrome, headless: true });
    const page = await browser.newPage(); await page.setViewport({ width: 512, height: 512, deviceScaleFactor: 1 });
    for (const [name, svg] of todo) {
      await page.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
      await page.screenshot({ path: path.join(dir, name + '.png'), omitBackground: true });
    }
    await browser.close(); console.log('rendered', todo.map(t => t[0]).join(' '));
  }
} else { console.log('usage: node icon.mjs search <word> [set] | render <outDir> <Name> ...'); }
