// static/js/scene.js
// ---------------------------------------------------------------------------
// The SCENE owns the single PixiJS renderer and everything drawn on it.
//
// Think of Pixi like a stack of transparent sheets ("containers"). We keep a
// few named sheets so each stage can draw onto the right one and wipe just its
// own sheet when it leaves:
//
//   background  -> the starfield / planet backdrop (drawn once, rarely cleared)
//   world       -> the stage's sprites (planets, ships, crew, enemy)
//   effects     -> short-lived things on top (a phaser beam, a hit flash)
//
// The rest of the game never touches Pixi directly -- it calls these helpers.
// ---------------------------------------------------------------------------

import * as PIXI from "pixi.js";

// The logical size we design against. Pixi scales the canvas to fit its box,
// so we can always place things using these coordinates regardless of screen.
export const WIDTH = 960;
export const HEIGHT = 540;

let app = null; // the one PIXI.Application
const layers = {}; // { background, world, effects } containers
let starfield = null; // kept so we can animate it (warp streaks etc.)

// Boot Pixi onto the <canvas> in index.html. Call once, await it.
export async function initScene() {
  app = new PIXI.Application();
  await app.init({
    canvas: document.getElementById("stage-canvas"),
    width: WIDTH,
    height: HEIGHT,
    background: "#02030a", // deep space
    antialias: true,
    resolution: Math.min(window.devicePixelRatio || 1, 2),
    autoDensity: true,
  });

  // Create the named layers in draw order (first added = furthest back).
  for (const name of ["background", "world", "effects"]) {
    const c = new PIXI.Container();
    layers[name] = c;
    app.stage.addChild(c);
  }

  starfield = makeStarfield();
  layers.background.addChild(starfield);

  return app;
}

// Give modules access when they genuinely need the raw app (e.g. the ticker).
export function getApp() {
  return app;
}

// Show a real image (e.g. NASA's Astronomy Picture of the Day) faded in behind
// the starfield. Best-effort: if the image can't be loaded, we just keep the
// plain starfield. `clearStage()` does NOT remove it (it lives in background).
let backdropSprite = null;
export async function setBackdrop(url) {
  if (!url || !app) return;
  try {
    const texture = await PIXI.Assets.load(url);
    if (backdropSprite) backdropSprite.destroy();
    backdropSprite = new PIXI.Sprite(texture);
    backdropSprite.width = WIDTH;
    backdropSprite.height = HEIGHT;
    backdropSprite.alpha = 0.35; // dim so sprites/text stay readable
    layers.background.addChildAt(backdropSprite, 0); // behind the stars
  } catch {
    /* keep the starfield */
  }
}

// Remove the backdrop (e.g. when leaving Stage 2).
export function clearBackdrop() {
  if (backdropSprite) {
    backdropSprite.destroy();
    backdropSprite = null;
  }
}

export function getLayer(name) {
  return layers[name];
}

// Remove everything a stage drew, so the next stage starts from a clean scene.
// We keep the starfield (it belongs to `background`); world + effects are wiped.
export function clearStage() {
  for (const name of ["world", "effects"]) {
    layers[name].removeChildren().forEach((child) => child.destroy({ children: true }));
  }
}

// ---------------------------------------------------------------------------
// Starfield: a cloud of little white dots. `setWarp(true)` stretches them into
// streaks by scaling the whole layer horizontally -- a cheap, convincing warp.
// ---------------------------------------------------------------------------
function makeStarfield() {
  const g = new PIXI.Graphics();
  // A fixed, seeded-looking spread (no Math.random needed -> same every run).
  for (let i = 0; i < 160; i++) {
    const x = (i * 61) % WIDTH;
    const y = (i * 137) % HEIGHT;
    const r = (i % 3) * 0.6 + 0.6;
    g.circle(x, y, r).fill({ color: 0xffffff, alpha: 0.25 + (i % 5) * 0.12 });
  }
  return g;
}

let warping = false;
export function setWarp(on) {
  warping = on;
}

// Called every frame by main.js's ticker to animate the starfield.
export function tickScene(deltaMS) {
  if (!starfield) return;
  const speed = warping ? 0.9 : 0.02; // pixels/ms drift, faster at warp
  starfield.x -= speed * deltaMS;
  // Wrap the drift so it loops seamlessly.
  if (starfield.x <= -WIDTH) starfield.x = 0;
  starfield.scale.x = warping ? 3 : 1;
  starfield.alpha = warping ? 0.9 : 1;
}
