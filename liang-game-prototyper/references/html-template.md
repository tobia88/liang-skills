# index.html Skeleton and Patterns

The skeleton below is the starting point for every 2D prototype. Replace the demo
mechanic with the prototype's own; keep the boilerplate sections (scaling, input, loop,
HUD, restart) intact unless the prototype has a real reason to differ.

## Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Grapple Platformer — prototype</title>
<style>
  html, body { margin: 0; height: 100%; background: #101418; overflow: hidden; }
  body { display: grid; place-items: center; }
  canvas { background: #181f26; image-rendering: pixelated; }
  #hud { position: fixed; top: 8px; left: 8px; color: #7fd4c0;
         font: 12px/1.5 monospace; white-space: pre; pointer-events: none; }
</style>
</head>
<body>
<canvas id="game"></canvas>
<div id="hud"></div>
<script>
'use strict';

// ===================== CONFIG — every tunable lives here =====================
const CONFIG = {
  logicalW: 960,        // px, fixed logical resolution
  logicalH: 540,        // px
  gravity: 2200,        // px/s^2
  moveSpeed: 420,       // px/s, horizontal ground speed
  jumpVel: 820,         // px/s, initial jump impulse (positive = up)
  // ... one commented line per tunable, grouped by system
};

// ===================== Boilerplate: canvas + scaling =====================
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const hud = document.getElementById('hud');
canvas.width = CONFIG.logicalW;
canvas.height = CONFIG.logicalH;
function fit() {
  const s = Math.min(innerWidth / CONFIG.logicalW, innerHeight / CONFIG.logicalH);
  canvas.style.width  = Math.floor(CONFIG.logicalW * s) + 'px';
  canvas.style.height = Math.floor(CONFIG.logicalH * s) + 'px';
}
addEventListener('resize', fit); fit();

// ===================== Boilerplate: input =====================
const keys = new Set();
let debugHud = true;
addEventListener('keydown', e => {
  if (e.code === 'KeyR') reset();
  if (e.code === 'Backquote') debugHud = !debugHud;
  keys.add(e.code);
  unlockAudio();                 // see audio pattern below
});
addEventListener('keyup', e => keys.delete(e.code));
// For mouse aiming: track canvas-space coords, dividing out the CSS scale.
// const mouse = { x: 0, y: 0, down: false };
// canvas.addEventListener('mousemove', e => {
//   const r = canvas.getBoundingClientRect();
//   mouse.x = (e.clientX - r.left) * (CONFIG.logicalW / r.width);
//   mouse.y = (e.clientY - r.top)  * (CONFIG.logicalH / r.height);
// });

// ===================== Game state =====================
let state;
function reset() {
  state = {
    // all mutable game state in one object so R fully restarts
  };
}
reset();

// ===================== Update / render =====================
function update(dt) {
  // semi-implicit Euler: apply acceleration to velocity FIRST, then move.
  // vel += acc * dt;  pos += vel * dt;
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // draw world, then UI text (title + controls in a corner)
}

// ===================== Boilerplate: main loop =====================
let last = performance.now();
function frame(now) {
  const dt = Math.min((now - last) / 1000, 1 / 30); // clamp: tab-back, hitches
  last = now;
  update(dt);
  render();
  hud.textContent = debugHud
    ? `fps ${Math.round(1 / dt)}\n` // + key live values worth watching while tuning
    : '';
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
```

## Patterns

### Loading shared pool assets (file:// safe)

```js
function sprite(name) {            // name e.g. 'player-mech-32.svg'
  const img = new Image();
  img.src = '../shared_assets/' + name;
  return img;
}
const playerImg = sprite('player-mech-32.svg');
// In render(): draw a fallback shape until loaded, so the prototype is
// playable even while images stream in or if a file is missing.
if (playerImg.complete && playerImg.naturalWidth) {
  ctx.drawImage(playerImg, x, y, w, h);
} else {
  ctx.fillStyle = '#e85d75'; ctx.fillRect(x, y, w, h);
}
```

Audio files from the pool: `new Audio('../shared_assets/jump-blip.wav')`. Clone before
play if it can retrigger fast: `audioEl.cloneNode().play()`.

### Synthesized sound (zero files)

For one-off bleeps not worth a pool file, synthesize with WebAudio. Browsers require a
user gesture before audio starts — hence `unlockAudio()` in the keydown handler:

```js
let actx = null;
function unlockAudio() { if (!actx) actx = new AudioContext(); }
function beep(freq = 440, dur = 0.08, type = 'square', vol = 0.15) {
  if (!actx) return;
  const o = actx.createOscillator(), g = actx.createGain();
  o.type = type; o.frequency.value = freq;
  g.gain.setValueAtTime(vol, actx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001, actx.currentTime + dur);
  o.connect(g).connect(actx.destination);
  o.start(); o.stop(actx.currentTime + dur);
}
```

### Feel and tuning

- Semi-implicit Euler (velocity before position) keeps jump heights consistent across
  frame rates; with the clamped dt it is stable enough for any feel prototype.
- If the mechanic is *extremely* timing-sensitive (fighting-game cancels, pixel-perfect
  physics), switch to a fixed-timestep accumulator — otherwise don't bother.
- Surface the values being tuned on the debug HUD (current speed, cooldown remaining,
  state name). Watching numbers while feeling the mechanic is the whole point of the
  prototype.
- Always render the controls as small text in a canvas corner — the prototype must be
  self-explanatory when reopened weeks later.

### CDN libraries (only when genuinely needed)

3D or real physics may justify a library. Use a plain `<script src>` from a major CDN
(no ES module imports — they fail on `file://`), keep CONFIG + HUD + restart conventions
anyway, and record the network dependency in the README's "How to run".

## Pre-flight Checklist

Re-read the finished file and confirm:

1. Every identifier used is defined — especially CONFIG keys referenced in
   update/render vs. keys actually declared.
2. `reset()` recreates **all** mutable state; pressing R mid-game cannot leave stale
   references.
3. No `fetch()`/XHR, no `import`, no external file references except
   `../shared_assets/*` and an optional CDN `<script src>`.
4. Every shared asset drawn has a loaded-check + fallback shape.
5. dt is in seconds and clamped; all speeds/accelerations are per-second, not per-frame.
6. Controls listed on-canvas match the actual key handlers, including R and backquote.
7. Win/lose (if any) is reachable and communicates itself on screen.
