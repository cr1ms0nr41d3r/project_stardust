// static/js/main.js
// ---------------------------------------------------------------------------
// The ORCHESTRATOR and entry point. Its jobs:
//   1. Boot the Pixi scene and load the sprite assets (once).
//   2. Run a per-frame ticker so the starfield (and any effects) animate.
//   3. Own the STATE MACHINE: show one stage at a time, and when a stage
//      finishes, decide which stage comes next.
//
// Each stage lives in its own module and exposes a single factory:
//     create(ctx) -> { unmount() }
// `ctx` is the toolbox we hand every stage (scene helpers, the HTML overlay,
// the shared game state, and goStage() to move on). This keeps the stages
// "dumb": they render and report a result; main.js decides the flow.
// ---------------------------------------------------------------------------

import { initScene, getApp, clearStage, tickScene, setWarp } from "./scene.js";
import { loadAssets } from "./assets.js";
import { STAGES, newGameState } from "./state.js";

import * as stage1 from "./stage1.js";
import * as stage2 from "./stage2.js";
import * as stage3 from "./stage3.js";
import * as ending from "./ending.js";

// Which module handles which stage.
const STAGE_MODULES = {
  [STAGES.STAGE1]: stage1,
  [STAGES.STAGE2]: stage2,
  [STAGES.STAGE3]: stage3,
  [STAGES.ENDING]: ending,
};

// The control panel below the viewscreen. Stage modules render all their
// buttons/text here (it's deliberately separate from the sprite canvas above).
const overlay = document.getElementById("ui-panel");
const stageLabel = document.getElementById("stage-label");
const stageHint = document.getElementById("stage-hint");

let gameState = newGameState();
let current = null; // the mounted stage's { unmount } handle

// Update the little status bar under the stage.
function setStatus(label, hint = "") {
  stageLabel.textContent = label;
  stageHint.textContent = hint;
}

// The heart of the state machine: leave the current stage, then mount the next.
// `payload` lets a stage pass data forward (e.g. the chosen planet).
function goStage(next, payload = {}) {
  // 1. Tear down whatever is on screen now.
  if (current && current.unmount) current.unmount();
  overlay.replaceChildren(); // wipe all HTML controls
  clearStage(); // wipe Pixi world + effects layers
  setWarp(false);

  gameState.stage = next;

  // 2. Mount the next stage with a fresh toolbox.
  const mod = STAGE_MODULES[next];
  if (!mod) {
    setStatus("Error", `No module for stage ${next}`);
    return;
  }
  current = mod.create({
    overlay,
    state: gameState,
    goStage,
    setStatus,
    setWarp,
  });
}

// Restart the whole game from Stage 1 (used by the ending screen).
export function restart() {
  gameState = newGameState();
  goStage(STAGES.STAGE1);
}
// Expose restart so the ending module can call it without a circular import.
window.__restartGame = restart;

async function boot() {
  setStatus("Booting…", "Loading the ship's systems");
  await initScene();
  await loadAssets();

  // Per-frame animation loop. Pixi's ticker gives us the ms since last frame.
  getApp().ticker.add((ticker) => tickScene(ticker.deltaMS));

  // Off we go: begin at Stage 1.
  goStage(STAGES.STAGE1);
}

boot();
