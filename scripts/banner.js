// YouTube banner (2560x1440, everything important inside the 1546x423 safe area in the middle). Writes assets/banner_es.png / banner_en.png
// usage: node banner.js
const { createCanvas, GlobalFonts, loadImage } = require('@napi-rs/canvas');
const fs = require('fs'), path = require('path');
GlobalFonts.registerFromPath(path.join(__dirname, '..', 'assets', 'fonts', 'Quicksand-Bold.ttf'), 'QB');
const A = path.join(__dirname, '..', 'assets');
(async () => {
  const logo = await loadImage(path.join(A, 'logo.png'));
  for (const [lang, name, line] of [['es', 'ADENTRO TV', 'Lo que pasa dentro de tu cuerpo · shorts todos los días'],
                                    ['en', 'INSIDE TV', 'What happens inside your body · new shorts every day']]) {
    const W = 2560, H = 1440, cv = createCanvas(W, H), c = cv.getContext('2d');
    const g = c.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#0b0f1a'); g.addColorStop(1, '#2a0b18'); c.fillStyle = g; c.fillRect(0, 0, W, H);
    // floating "cells" for texture
    for (let i = 0; i < 70; i++) { const x = (i * 977) % W, y = (i * 613) % H, r = 20 + (i * 37) % 90;
      c.fillStyle = `rgba(255,77,109,${0.04 + (i % 5) * 0.02})`; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill(); }
    // fit logo + texts inside the safe area (x 507–2053, y 508–931) that every device shows
    const SX = 507, SW = 1546, L = 300, gap = 50;
    let t = 170, sub = 56;
    c.font = `${t}px QB`; let tw = c.measureText(name).width; c.font = `${sub}px QB`; let sw = c.measureText(line).width;
    const k = Math.min(1, (SW - L - gap) / Math.max(tw, sw)); t *= k; sub *= k; tw *= k; sw *= k;
    const x0 = SX + (SW - (L + gap + Math.max(tw, sw))) / 2;
    c.drawImage(logo, x0, 720 - L / 2, L, L);
    c.textBaseline = 'middle'; c.fillStyle = '#ffffff'; c.font = `${t}px QB`; c.fillText(name, x0 + L + gap, 720 - sub * 0.9);
    c.fillStyle = '#ff8fa3'; c.font = `${sub}px QB`; c.fillText(line, x0 + L + gap, 720 + t * 0.45);
    fs.writeFileSync(path.join(A, `banner_${lang}.png`), cv.toBuffer('image/png'));
  }
  console.log('banners listos');
})();
