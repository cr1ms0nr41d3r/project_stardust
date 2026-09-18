// static/js/assets.js
// ---------------------------------------------------------------------------
// ASSETS: how we get pictures (sprites) onto the screen.
//
// Two rules keep this simple and crash-proof:
//   1. We try to load real PNGs listed in MANIFEST from /static/assets/...
//   2. If a file is missing or fails to load, we AUTO-GENERATE a placeholder
//      (a coloured shape with a text label). So the whole game is playable with
//      zero art, and you can drop real PNGs in later without touching any code.
//
// Everything asks for a picture by a short "alias" (e.g. "planet_vega"). The
// helper getTexture(alias, kind, label) always returns *something* drawable.
// ---------------------------------------------------------------------------

import * as PIXI from "pixi.js";
import { getApp } from "./scene.js";

// alias -> file url. Real sprites go in /static/assets/. Anything NOT listed
// here (or that fails to load) falls back to a generated placeholder, so this
// list can stay small and grow as real art is added.
const MANIFEST = {
  // Real image files that ship with the game, under /static/assets/. To use
  // different art, drop a PNG in that folder and point its alias here -- no
  // other code changes. Any alias NOT listed (or that fails to load) falls back
  // to a generated placeholder, so nothing ever breaks.
  enterprise: "/static/assets/ships/enterprise.png",
  klingon: "/static/assets/enemy/klingon.png",
  rakelli: "/static/assets/enemy/rakelli.png",
  // Stage 2 planets are REAL exoplanets. The server downloads a real NASA image
  // for each into these paths on first run (if it can reach NASA); until then,
  // or if offline, the generated placeholder is drawn automatically.
  planet_trappist_e: "/static/assets/planets/trappist_e.png",
  planet_verdanya: "/static/assets/planets/trappist_e.png",
  planet_kepler_452b: "/static/assets/planets/kepler_452b.png",
  planet_cnc_55e: "/static/assets/planets/cnc_55e.png",
  planet_hd_209458b: "/static/assets/planets/hd_209458b.png",
  planet_proxima_b: "/static/assets/planets/proxima_b.png",
  planet_gj_1214b: "/static/assets/planets/gj_1214b.png",
};

const loaded = {}; // alias -> PIXI.Texture (real, successfully loaded)
const placeholderCache = {}; // key -> PIXI.Texture (generated once, reused)

// Load every real asset in the MANIFEST. Missing files are tolerated: we log a
// warning and simply fall back to placeholders at draw time.
export async function loadAssets() {
  const entries = Object.entries(MANIFEST);
  await Promise.all(
    entries.map(async ([alias, url]) => {
      try {
        loaded[alias] = await PIXI.Assets.load(url);
      } catch (err) {
        console.warn(`[assets] "${alias}" (${url}) failed to load — using a placeholder.`, err);
      }
    })
  );
}

// A stable colour per alias, so the same thing always gets the same placeholder
// colour (no randomness -> identical every run).
function colourFor(alias) {
  let h = 0;
  for (let i = 0; i < alias.length; i++) h = (h * 31 + alias.charCodeAt(i)) & 0xffffff;
  // Keep it bright-ish by forcing the top bits on.
  return (h | 0x404040) & 0xffffff;
}

// Build (and cache) a placeholder texture for a given kind + label + colour.
// kind decides the SHAPE so different things read differently at a glance.
function makePlaceholder(alias, kind, label) {
  const key = `${kind}:${label}:${alias}`;
  if (placeholderCache[key]) return placeholderCache[key];

  const app = getApp();
  const colour = colourFor(alias);
  const g = new PIXI.Graphics();
  const S = 120; // placeholder box size

  if (kind === "planet") {
    g.circle(S / 2, S / 2, S / 2 - 4).fill({ color: colour });
    g.circle(S / 2, S / 2, S / 2 - 4).stroke({ color: 0xffffff, width: 2, alpha: 0.5 });
  } else if (kind === "ship") {
    g.moveTo(S / 2, 6).lineTo(S - 6, S - 10).lineTo(6, S - 10).closePath().fill({ color: colour });
  } else if (kind === "enemy") {
    g.moveTo(6, S / 2).lineTo(S / 2, 8).lineTo(S - 6, S / 2).lineTo(S / 2, S - 8).closePath().fill({ color: 0xcc3344 });
  } else {
    // crew / ui / anything else: a rounded rectangle portrait.
    g.roundRect(6, 6, S - 12, S - 12, 12).fill({ color: colour });
    g.roundRect(6, 6, S - 12, S - 12, 12).stroke({ color: 0xffffff, width: 2, alpha: 0.5 });
  }

  const container = new PIXI.Container();
  container.addChild(g);

  if (label) {
    const text = new PIXI.Text({
      text: label,
      style: { fill: 0xffffff, fontSize: 14, fontFamily: "monospace", align: "center", wordWrap: true, wordWrapWidth: S - 8 },
    });
    text.anchor.set(0.5);
    text.x = S / 2;
    text.y = S / 2;
    container.addChild(text);
  }

  const texture = app.renderer.generateTexture(container);
  container.destroy({ children: true });
  placeholderCache[key] = texture;
  return texture;
}

// The one function the rest of the game uses. Always returns a usable texture:
// the real one if it loaded, otherwise a generated placeholder.
//   alias : which asset (also seeds the placeholder colour)
//   kind  : "planet" | "ship" | "enemy" | "crew" | "ui"  (placeholder shape)
//   label : short text drawn on the placeholder (ignored if real art loaded)
export function getTexture(alias, kind = "ui", label = "") {
  return loaded[alias] || makePlaceholder(alias, kind, label);
}

// Convenience: build a ready-to-place sprite, centred on its anchor.
export function makeSprite(alias, kind = "ui", label = "") {
  const sprite = new PIXI.Sprite(getTexture(alias, kind, label));
  sprite.anchor.set(0.5);
  return sprite;
}
