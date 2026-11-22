// Render a vertical short of @adentro-tv: Pixabay clip background (bg.mp4) + graphics drawn per frame on a canvas
// (brand, hook card, big word-by-word captions, progress bar, closing call to follow).
// usage: node render.js <ffmpeg> <timeline.json> <audio.wav> <out.mp4> [previewTimesCSV previewDir]
const { createCanvas, GlobalFonts, loadImage } = require('@napi-rs/canvas');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
GlobalFonts.registerFromPath(path.join(__dirname, '..', 'assets', 'fonts', 'Quicksand-Bold.ttf'), 'QB');
for (const f of ['/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf']) if (fs.existsSync(f)) GlobalFonts.registerFromPath(f, 'EMO');

const [ffm, tlFile, audio, out, prevTimes, prevDir] = process.argv.slice(2);
const TL = JSON.parse(fs.readFileSync(tlFile, 'utf8'));
const W = 1080, H = 1920, FPS = 30;
const C = { white: '#ffffff', ink: '#0b0f1a', coral: '#ff4d6d', cyan: '#3ee6ff', yellow: '#ffd23f' };
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const easeOut = t => 1 - Math.pow(1 - t, 3);
const easeBack = t => { const c = 1.7; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
const prog = (t, a, b) => clamp((t - a) / (b - a));
const norm = s => s.toLowerCase().replace(/[.,:;¿?¡!…"()]/g, '');
let LOGO = null;

function shade(ctx) {
  // darker top and bottom so white text always reads over any clip
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, 'rgba(0,0,0,0.55)'); g.addColorStop(0.22, 'rgba(0,0,0,0.05)');
  g.addColorStop(0.55, 'rgba(0,0,0,0.10)'); g.addColorStop(1, 'rgba(0,0,0,0.60)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}

function brand(ctx) {
  const x = 56, y = 120;
  ctx.save();
  if (LOGO) ctx.drawImage(LOGO, x, y - 38, 76, 76);
  ctx.font = '44px QB'; ctx.fillStyle = C.white; ctx.textBaseline = 'middle';
  ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 12;
  ctx.fillText(TL.brand || 'ADENTRO TV', x + (LOGO ? 92 : 0), y + 2);
  ctx.restore();
}

function wrap(ctx, s, maxW) {
  const out = [''];
  for (const w of s.split(' ')) { const t = out[out.length - 1] ? out[out.length - 1] + ' ' + w : w; if (ctx.measureText(t).width > maxW && out[out.length - 1]) out.push(w); else out[out.length - 1] = t; }
  return out;
}

function hook(ctx, t) {
  const a = prog(t, 0.05, 0.4), z = 1 - prog(t, 2.6, 2.95);
  if (a <= 0 || z <= 0) return;
  const size = 76; ctx.save(); ctx.font = `${size}px QB, EMO`;
  const rows = wrap(ctx, TL.hook.toUpperCase(), 900), lh = size * 1.18;
  const h = rows.length * lh + 60, y = 360;
  ctx.globalAlpha = Math.min(1, z * 1.5);
  ctx.translate(W / 2, y + h / 2); const s = 0.8 + 0.2 * easeBack(a); ctx.scale(s, s); ctx.translate(-W / 2, -(y + h / 2));
  ctx.fillStyle = C.yellow; ctx.beginPath(); ctx.roundRect(70, y, W - 140, h, 28); ctx.fill();
  ctx.fillStyle = C.ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  rows.forEach((r, i) => ctx.fillText(r, W / 2, y + 30 + lh * (i + 0.5)));
  ctx.restore();
}

function captions(ctx, t) {
  const cap = TL.captions.find(c => t >= c.start && t < c.end);
  if (!cap) return;
  const size = 104, y = 1240, k = easeBack(prog(t, cap.start, cap.start + 0.18));
  ctx.save(); ctx.font = `${size}px QB, EMO`; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  const ws = cap.words.map(w => w.text.toUpperCase()), sp = size * 0.28;
  let widths = ws.map(w => ctx.measureText(w).width), total = widths.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
  const sc = Math.min(1, 960 / total);
  ctx.translate(W / 2, y); ctx.scale(sc * (0.85 + 0.15 * k), sc * (0.85 + 0.15 * k));
  let x = -total / 2;
  cap.words.forEach((w, i) => {
    const on = t >= w.start, hot = TL.hi.includes(norm(w.text));
    ctx.lineWidth = 16; ctx.strokeStyle = 'rgba(0,0,0,0.92)'; ctx.strokeText(ws[i], x, 0);
    ctx.fillStyle = hot ? C.coral : on ? C.yellow : C.white; ctx.fillText(ws[i], x, 0);
    x += widths[i] + sp;
  });
  ctx.restore();
}

function progress(ctx, t) {
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.fillRect(0, 0, W, 12);
  ctx.fillStyle = C.coral; ctx.fillRect(0, 0, W * clamp(t / TL.duration), 12);
}

function cta(ctx, t) {
  const a = easeOut(prog(t, TL.duration - 1.6, TL.duration - 1.2));
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.font = '54px QB, EMO'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const w = ctx.measureText(TL.cta).width + 80, y = 1480 + (1 - a) * 40;
  ctx.fillStyle = C.coral; ctx.beginPath(); ctx.roundRect(W / 2 - w / 2, y - 50, w, 100, 50); ctx.fill();
  ctx.fillStyle = C.white; ctx.fillText(TL.cta, W / 2, y + 2); ctx.restore();
}

function draw(ctx, t) {
  ctx.clearRect(0, 0, W, H);
  shade(ctx); brand(ctx); hook(ctx, t);
  if (t > 2.7 || !TL.hook) captions(ctx, t);  // the hook card owns the first seconds
  cta(ctx, t); progress(ctx, t);
}

(async () => {
  try { LOGO = await loadImage(path.join(__dirname, '..', 'assets', 'logo.png')); } catch { LOGO = null; }
  const cv = createCanvas(W, H), ctx = cv.getContext('2d');
  if (prevTimes) {
    fs.mkdirSync(prevDir, { recursive: true });
    for (const s of prevTimes.split(',')) { draw(ctx, parseFloat(s)); fs.writeFileSync(`${prevDir}/g_${s}.png`, cv.toBuffer('image/png')); }
    return;
  }
  const ff = spawn(ffm, ['-y', '-v', 'error', '-i', TL.bg, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-', '-i', audio,
    '-filter_complex', '[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]', '-map', '[v]', '-map', '2:a',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.ceil(TL.duration * FPS);
  for (let f = 0; f < N; f++) {
    draw(ctx, f / FPS);
    if (!ff.stdin.write(Buffer.from(ctx.getImageData(0, 0, W, H).data.buffer))) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('listo', out);
})();
