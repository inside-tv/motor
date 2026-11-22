// Draw the channel mark: a coral cell with its nucleus. Writes assets/logo.png (256 px, for videos) and assets/perfil_es.png and perfil_en.png (800 px).
// usage: node logo.js
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const fs = require('fs'), path = require('path');
GlobalFonts.registerFromPath(path.join(__dirname, '..', 'assets', 'fonts', 'Quicksand-Bold.ttf'), 'QB');
function mark(S, name) {
  const cv = createCanvas(S, S), c = cv.getContext('2d'), r = S / 2;
  if (name) { c.fillStyle = '#0b0f1a'; c.fillRect(0, 0, S, S); }
  const R = name ? S * 0.30 : S * 0.48, cy = name ? S * 0.40 : r;
  const g = c.createRadialGradient(r - R * 0.3, cy - R * 0.3, R * 0.1, r, cy, R);
  g.addColorStop(0, '#ff8fa3'); g.addColorStop(1, '#ff4d6d');
  c.fillStyle = g; c.beginPath(); c.arc(r, cy, R, 0, Math.PI * 2); c.fill();
  c.strokeStyle = 'rgba(255,255,255,0.85)'; c.lineWidth = R * 0.07; c.beginPath(); c.arc(r, cy, R * 0.82, 0, Math.PI * 2); c.stroke();
  c.fillStyle = '#ffffff'; c.beginPath(); c.arc(r + R * 0.18, cy - R * 0.12, R * 0.30, 0, Math.PI * 2); c.fill();
  c.fillStyle = '#ff4d6d'; c.beginPath(); c.arc(r + R * 0.24, cy - R * 0.18, R * 0.11, 0, Math.PI * 2); c.fill();
  if (name) { c.fillStyle = '#ffffff'; c.font = `${S * 0.13}px QB`; c.textAlign = 'center'; c.fillText(name, r, S * 0.88); }
  return cv.toBuffer('image/png');
}
fs.writeFileSync(path.join(__dirname, '..', 'assets', 'logo.png'), mark(256, false));
fs.writeFileSync(path.join(__dirname, '..', 'assets', 'perfil_es.png'), mark(800, 'ADENTRO TV'));
fs.writeFileSync(path.join(__dirname, '..', 'assets', 'perfil_en.png'), mark(800, 'INSIDE TV'));
console.log('logo listo');
// round avatar without text: YouTube shows the profile picture as a small circle, where a name would be unreadable
{ const S = 800, cv = createCanvas(S, S), c = cv.getContext('2d');
  c.fillStyle = '#0b0f1a'; c.fillRect(0, 0, S, S);
  const R = S * 0.36, r = S / 2, g = c.createRadialGradient(r - R * 0.3, r - R * 0.3, R * 0.1, r, r, R);
  g.addColorStop(0, '#ff8fa3'); g.addColorStop(1, '#ff4d6d'); c.fillStyle = g; c.beginPath(); c.arc(r, r, R, 0, Math.PI * 2); c.fill();
  c.strokeStyle = 'rgba(255,255,255,0.85)'; c.lineWidth = R * 0.07; c.beginPath(); c.arc(r, r, R * 0.82, 0, Math.PI * 2); c.stroke();
  c.fillStyle = '#fff'; c.beginPath(); c.arc(r + R * 0.18, r - R * 0.12, R * 0.30, 0, Math.PI * 2); c.fill();
  c.fillStyle = '#ff4d6d'; c.beginPath(); c.arc(r + R * 0.24, r - R * 0.18, R * 0.11, 0, Math.PI * 2); c.fill();
  fs.writeFileSync(path.join(__dirname, '..', 'assets', 'avatar.png'), cv.toBuffer('image/png')); }
