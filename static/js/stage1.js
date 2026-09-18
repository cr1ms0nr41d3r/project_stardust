// static/js/stage1.js
// ---------------------------------------------------------------------------
// STAGE 1 — the card-battle tutorial. NO AI: it is pure client-side logic.
//
// A Klingon scout jumps you on the way to the mission. You play one card per
// round (see cardBattle.js) until someone's hull hits zero. Winning moves you
// to Stage 2; losing simply restarts the fight so the player can learn it.
//
// This module is the "controller": it owns the DOM/overlay + sprites for the
// battle and delegates every rule to the deterministic engine.
// ---------------------------------------------------------------------------

import { getLayer, WIDTH, HEIGHT } from "./scene.js";
import { makeSprite } from "./assets.js";
import { CARDS, createBattle } from "./cardBattle.js";
import { STAGES } from "./state.js";
import { el, panel, bar } from "./ui.js";

// The tutorial fight's settings (easy, short, teaches the mechanics).
const TUTORIAL = {
  playerHP: 20,
  enemyHP: 15,
  enemyName: "Klingon scout",
  enemyScript: ["attack", "attack", "charge", "heavy"],
};

export function create(ctx) {
  const { overlay, goStage, setStatus } = ctx;
  setStatus("Stage 1 — Ambush!", "Play a card each round. Reduce the enemy hull to zero.");

  const battle = createBattle(TUTORIAL);

  // ---- Sprites on the Pixi scene: our ship (left) vs the enemy (right). ----
  const world = getLayer("world");
  const ship = makeSprite("enterprise", "ship", "Enterprise");
  ship.x = WIDTH * 0.24;
  ship.y = HEIGHT * 0.42;
  ship.scale.set(1.3);
  const enemy = makeSprite("klingon", "enemy", "Klingon");
  enemy.x = WIDTH * 0.76;
  enemy.y = HEIGHT * 0.42;
  enemy.scale.set(1.1);
  world.addChild(ship, enemy);

  // A quick red-tint "hit" flash on a sprite.
  function flash(sprite) {
    sprite.tint = 0xff5555;
    setTimeout(() => (sprite.tint = 0xffffff), 200);
  }

  // ---- The HTML overlay: HP bars, a log, and the card buttons. ----
  const enemyBar = bar(TUTORIAL.enemyName, "enemy");
  const playerBar = bar("Enterprise", "friendly");
  const logEl = el("div", { class: "battle-log" });
  const handEl = el("div", { class: "card-hand" });

  const box = panel("Red Alert — Battle Stations", "battle-panel");
  box.append(enemyBar.root, playerBar.root, logEl, handEl);
  overlay.append(box);

  function refreshBars() {
    enemyBar.set(battle.state.enemyHP / battle.state.enemyMaxHP, `${battle.state.enemyHP}/${battle.state.enemyMaxHP}`);
    playerBar.set(battle.state.playerHP / battle.state.playerMaxHP, `${battle.state.playerHP}/${battle.state.playerMaxHP}`);
  }

  function log(line, side = "system") {
    logEl.append(el("div", { class: `log-line ${side}`, text: line }));
    logEl.scrollTop = logEl.scrollHeight;
  }

  // Draw the four card buttons; disabled ones (e.g. Torpedo recharging) grey out.
  function renderHand() {
    handEl.replaceChildren();
    for (const id of ["phaser", "torpedo", "shield", "evade"]) {
      const card = CARDS[id];
      const usable = battle.canUse(id);
      const btn = el(
        "button",
        {
          class: `card card-${card.type}${usable ? "" : " disabled"}`,
          onclick: usable ? () => onPlay(id) : undefined,
        },
        [el("div", { class: "card-name", text: card.name }), el("div", { class: "card-text", text: card.text })]
      );
      if (!usable) btn.disabled = true;
      handEl.append(btn);
    }
  }

  function onPlay(id) {
    const events = battle.playCard(id);
    for (const e of events) {
      log(e.text, e.side);
      if (e.side === "player" && e.card && CARDS[e.card].damage) flash(enemy);
      if (e.side === "enemy" && !/dodge|charging/.test(e.text)) flash(ship);
    }
    refreshBars();

    if (battle.state.over) {
      renderEndButtons(battle.state.result);
    } else {
      renderHand();
    }
  }

  // When the fight ends, swap the hand for a Continue / Try again button.
  function renderEndButtons(result) {
    handEl.replaceChildren();
    if (result === "WIN") {
      setStatus("Stage 1 complete!", "Victory — plotting course to the survey system.");
      handEl.append(
        el("button", { class: "big-btn", onclick: () => goStage(STAGES.STAGE2) }, "Warp to the survey mission →")
      );
    } else {
      setStatus("Stage 1 — Defeated", "Your hull failed. Regroup and try the battle again.");
      handEl.append(
        el("button", { class: "big-btn", onclick: () => goStage(STAGES.STAGE1) }, "↻ Try the battle again")
      );
    }
  }

  // First paint.
  log("A Klingon scout decloaks off the port bow. Red alert!");
  refreshBars();
  renderHand();

  // Nothing to tear down beyond what main.js already clears (overlay + scene).
  return { unmount() {} };
}
