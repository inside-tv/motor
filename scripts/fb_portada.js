// Facebook page cover (1640x924): desktop crops it to the middle 1640x624 band, mobile shows it whole,
// so logo and texts stay inside that band. Writes assets/portada_fb_es.png / portada_fb_en.png
// usage: node fb_portada.js
const { createCanvas, GlobalFonts, loadImage } = require('@napi-rs/canvas');
const fs = require('fs'), path = require('path');
GlobalFonts.registerFromPath(path.join(__dirname, '..', 'assets', 'fonts', 'Quicksand-Bold.ttf'), 'QB');
const A = path.join(__dirname, '..', 'assets');
(async () => {
  const logo = await loadImage(path.join(A, 'logo.png'));
  for (const [lang, name, line] of [['es', 'ADENTRO TV', 'Lo que pasa dentro de tu cuerpo'],
                                    ['en', 'INSIDE TV', 'What happens inside your body']]) {
    const W = 1640, H = 924, cv = createCanvas(W, H), c = cv.getContext('2d');
    const g = c.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#0b0f1a'); g.addColorStop(1, '#2a0b18'); c.fillStyle = g; c.fillRect(0, 0, W, H);
    for (let i = 0; i < 45; i++) { const x = (i * 977) % W, y = (i * 613) % H, r = 14 + (i * 37) % 60;
      c.fillStyle = `rgba(255,77,109,${0.04 + (i % 5) * 0.02})`; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill(); }
    const L = 230, gap = 40, maxW = 1300;
    let t = 130, sub = 50;
    c.font = `${t}px QB`; let tw = c.measureText(name).width; c.font = `${sub}px QB`; let sw = c.measureText(line).width;
    const k = Math.min(1, (maxW - L - gap) / Math.max(tw, sw)); t *= k; sub *= k; tw *= k; sw *= k;
    const x0 = (W - (L + gap + Math.max(tw, sw))) / 2, cy = H / 2;
    c.drawImage(logo, x0, cy - L / 2, L, L);
    c.textBaseline = 'middle'; c.fillStyle = '#ffffff'; c.font = `${t}px QB`; c.fillText(name, x0 + L + gap, cy - sub * 0.8);
    c.fillStyle = '#ff8fa3'; c.font = `${sub}px QB`; c.fillText(line, x0 + L + gap, cy + t * 0.45);
    fs.writeFileSync(path.join(A, `portada_fb_${lang}.png`), cv.toBuffer('image/png'));
  }
  console.log('portadas listas');
})();
