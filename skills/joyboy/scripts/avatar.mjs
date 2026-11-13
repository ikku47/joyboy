// joyboy avatars: illustrated people from DiceBear (dicebear.com), generated locally, no network.
//   node avatar.mjs styles                                   list styles, licence, and how many mouths / eyes each has
//   node avatar.mjs options <style>                          list every option of a style (mouth, eyes, hair ...)
//   node avatar.mjs render <outDir> <name> <style> <seed> '<json options>' <mouths,comma> <eyes,comma> [px]
//        writes <name>__<mouth>__<eyes>.png (transparent) for every mouth x eyes pair: the frames of a talking face
import fs from 'node:fs'; import path from 'node:path';
import { createAvatar } from '@dicebear/core'; import * as col from '@dicebear/collection';
const [cmd, ...a] = process.argv.slice(2);
const en = (s, k) => s.schema?.properties?.[k]?.items?.enum || [];
if (cmd === 'styles') { for (const [n, s] of Object.entries(col)) console.log(n.padEnd(20), (s.meta?.license?.name || '?').padEnd(38), 'mouths', String(en(s, 'mouth').length).padEnd(3), 'eyes', en(s, 'eyes').length); }
else if (cmd === 'options') { for (const [k, v] of Object.entries(col[a[0]].schema.properties)) console.log(k.padEnd(22), (v.items?.enum || v.enum || [v.type]).join(' ')); }
else if (cmd === 'render') {
  const [dir, name, style, seed, json, mouths, eyes, px = '1024'] = a; const S = col[style]; if (!S) { console.error('no DiceBear style named ' + style); process.exit(1); }
  fs.mkdirSync(dir, { recursive: true }); const base = JSON.parse(json || '{}'); const todo = [];
  for (const m of mouths.split(',')) for (const e of eyes.split(',')) {
    for (const [k, v] of [['mouth', m], ['eyes', e]]) if (en(S, k).length && !en(S, k).includes(v)) { console.error(`style ${style} has no ${k} "${v}"; choices: ${en(S, k).join(' ')}`); process.exit(1); }
    todo.push([`${name}__${m}__${e}`, createAvatar(S, { seed, ...base, mouth: [m], eyes: [e], size: +px }).toString()]);
  }
  const puppeteer = (await import('puppeteer-core')).default;
  const chrome = process.env.CHROME_PATH || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(p => fs.existsSync(p));
  if (!chrome) { console.error('no Chrome-family browser found; set CHROME_PATH'); process.exit(2); }
  const browser = await puppeteer.launch({ executablePath: chrome, headless: true }); const page = await browser.newPage(); await page.setViewport({ width: +px, height: +px, deviceScaleFactor: 1 });
  for (const [n, svg] of todo) { fs.writeFileSync(path.join(dir, n + '.svg'), svg); await page.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`); await page.screenshot({ path: path.join(dir, n + '.png'), omitBackground: true }); }
  await browser.close(); console.log('rendered', todo.length, 'frames for', name);
} else console.log('usage: node avatar.mjs styles | options <style> | render <outDir> <name> <style> <seed> <json> <mouths> <eyes> [px]');
