// Render a vertical short of @adentro-tv: Pixabay clip background (bg.mp4) + graphics drawn per frame on a canvas
// (brand, hook card, big word-by-word captions, progress bar, closing call to follow).
// usage: node render.js <ffmpeg> <timeline.json> <audio.wav> <out.mp4> [previewTimesCSV previewDir]
const { createCanvas, GlobalFonts, loadImage } = require('@napi-rs/canvas');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
GlobalFonts.registerFromPath(path.join(__dirname, '..', 'assets', 'fonts', 'Quicksand-Bold.ttf'), 'QB');
GlobalFonts.registerFromPath(path.join(__dirname, '..', 'assets', 'fonts', 'Montserrat-Variable.ttf'), 'MS');  // captions + hook
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
  // no overlay over the clip: only a faint fade behind the brand (top) and the closing pill (bottom)
  const t = ctx.createLinearGradient(0, 0, 0, 260);
  t.addColorStop(0, 'rgba(0,0,0,0.28)'); t.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = t; ctx.fillRect(0, 0, W, 260);
  const b = ctx.createLinearGradient(0, H - 420, 0, H);
  b.addColorStop(0, 'rgba(0,0,0,0)'); b.addColorStop(1, 'rgba(0,0,0,0.30)');
  ctx.fillStyle = b; ctx.fillRect(0, H - 420, W, 420);
}

function brand(ctx) {
  const x = 56, y = 120;
  ctx.save();
  if (LOGO) ctx.drawImage(LOGO, x, y - 38, 76, 76);
  ctx.font = '800 40px MS'; ctx.fillStyle = C.white; ctx.textBaseline = 'middle';
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
  // clean big title over the clip (no card): white with a soft shadow and a short coral accent bar
  const size = 84; ctx.save(); ctx.font = `800 ${size}px MS, EMO`;
  const rows = wrap(ctx, TL.hook, 920), lh = size * 1.12;
  const h = rows.length * lh, y = 380;
  ctx.globalAlpha = Math.min(1, z * 1.5);
  ctx.translate(0, (1 - easeOut(a)) * 30);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.shadowColor = 'rgba(0,0,0,0.55)'; ctx.shadowBlur = 28; ctx.shadowOffsetY = 4;
  ctx.fillStyle = C.white; rows.forEach((r, i) => ctx.fillText(r, W / 2, y + lh * (i + 0.5)));
  ctx.shadowColor = 'transparent';
  const bw = 120 * easeOut(a); ctx.fillStyle = C.coral; ctx.beginPath(); ctx.roundRect(W / 2 - bw / 2, y + h + 22, bw, 10, 5); ctx.fill();
  ctx.restore();
}

function captions(ctx, t) {
  const cap = TL.captions.find(c => t >= c.start && t < c.end);
  if (!cap) return;
  // modern captions: sentence case, white with a soft shadow; the word being said sits on a coral pill
  const size = 92, y = 1240, k = easeOut(prog(t, cap.start, cap.start + 0.15));
  ctx.save(); ctx.font = `800 ${size}px MS, EMO`; ctx.textBaseline = 'middle';
  const ws = cap.words.map(w => w.text), sp = size * 0.26, padX = 18, padY = 14;
  let widths = ws.map(w => ctx.measureText(w).width), total = widths.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
  const sc = Math.min(1, 940 / total);
  ctx.translate(W / 2, y); ctx.scale(sc * (0.92 + 0.08 * k), sc * (0.92 + 0.08 * k)); ctx.globalAlpha = 0.4 + 0.6 * k;
  const cur = cap.words.findIndex((w, i) => t >= w.start && (i === cap.words.length - 1 || t < cap.words[i + 1].start));
  let x = -total / 2;
  cap.words.forEach((w, i) => {
    const hot = TL.hi.includes(norm(w.text));
    if (i === cur) {
      ctx.fillStyle = hot ? C.coral : 'rgba(255,77,109,0.92)';
      ctx.beginPath(); ctx.roundRect(x - padX, -size / 2 - padY + 6, widths[i] + padX * 2, size + padY * 2 - 6, 22); ctx.fill();
    }
    ctx.shadowColor = i === cur ? 'transparent' : 'rgba(0,0,0,0.75)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 3;
    ctx.fillStyle = i !== cur && hot ? '#ffb3c1' : C.white; ctx.fillText(ws[i], x, 4);
    x += widths[i] + sp;
  });
  ctx.restore();
}

function progress(ctx, t) {
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.fillRect(0, 0, W, 12);
  ctx.fillStyle = C.coral; ctx.fillRect(0, 0, W * clamp(t / TL.duration), 12);
}

function cta(ctx, t) {
  const s = TL.cta_start ?? TL.duration - 1.6;  // the pill shows up when the closing line is spoken
  const a = easeOut(prog(t, s, s + 0.4));
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.font = '800 50px MS, EMO'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
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
