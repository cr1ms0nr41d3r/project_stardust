// static/js/ending.js
// ---------------------------------------------------------------------------
// The ENDING screen. Shows how the mission turned out (based on the path taken
// and the outcome stored in game state) and offers a restart. No AI, no Pixi
// beyond the starfield -- just a summary panel.
// ---------------------------------------------------------------------------

import { el, panel } from "./ui.js";

// Flavour text keyed by "<PATH>_<OUTCOME>".
const ENDINGS = {
  DIPLOMACY_WIN: {
    title: "Peace Secured 🕊️",
    text: "Through patient negotiation you convinced the rival colonists to share the world. Two peoples will build a future here together. Starfleet logs a diplomatic triumph.",
  },
  DIPLOMACY_LOSE: {
    title: "Talks Collapsed",
    text: "Your arguments failed to move them, and they seized the colony by force before reinforcements arrived. The mission is lost — but no shots were fired by the Enterprise.",
  },
  FIGHT_WIN: {
    title: "World Defended ⚔️",
    text: "The Enterprise drove off the hostile fleet and secured the colony. Hard-won, but the settlers are safe. Starfleet logs a tactical victory.",
  },
  FIGHT_LOSE: {
    title: "The Line Broke",
    text: "The enemy fleet outlasted you and took the colony. The Enterprise limps home to fight another day.",
  },
};

export function create(ctx) {
  const { overlay, state, setStatus } = ctx;
  const key = `${state.path}_${state.outcome}`;
  const info = ENDINGS[key] || { title: "Mission Over", text: "The away mission has ended." };

  setStatus("Mission Complete", info.title);

  const box = panel(info.title, "ending-panel");
  box.append(el("p", { class: "ending-text", text: info.text }));
  box.append(
    el("button", { class: "big-btn", onclick: () => window.__restartGame() }, "↻ Play again from Stage 1")
  );
  overlay.append(box);

  return { unmount() {} };
}
