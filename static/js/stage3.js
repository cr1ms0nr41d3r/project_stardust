// static/js/stage3.js
// ---------------------------------------------------------------------------
// STAGE 3 — the finale. A rival colony fleet arrives to seize the habitable
// world you found. NO AI: the player chooses one of two scripted paths.
//
//   DIPLOMACY -> a branching dialogue tree (choices lead to a good or bad end)
//   FIGHT     -> the SAME card-battle engine as Stage 1, tuned tougher
//
// Either path ends by setting state.path + state.outcome and going to ENDING.
// ---------------------------------------------------------------------------

import { getLayer, WIDTH, HEIGHT } from "./scene.js";
import { makeSprite } from "./assets.js";
import { CARDS, createBattle } from "./cardBattle.js";
import { STAGES } from "./state.js";
import { el, panel, bar } from "./ui.js";

// The scripted negotiation. Each node has narration + options. An option's
// `goto` is another node id, or "WIN"/"LOSE" to end the talks.
const DIALOGUE = {
  start: {
    text: "A Rakelli colony fleet holds position over the world. Their leader, Vorne, hails you: “This planet is ours by need. Stand aside, Starfleet.”",
    options: [
      { label: "“Leave this system at once.”", goto: "hostile" },
      { label: "“Why do you need this world so badly?”", goto: "listen" },
      { label: "“We'll simply share it.” (offer immediately)", goto: "tooFast" },
    ],
  },
  listen: {
    text: "Vorne's tone softens. “Our star is dying — a slow cooling that has frozen our homeworld's oceans. We seek any world that can still hold liquid water. This one can.”",
    options: [
      { label: "“There is room here for both peoples. Let's share it.”", goto: "share" },
      { label: "“That's your problem. Find another world.”", goto: "dismiss" },
    ],
  },
  share: {
    text: "“Share it?” Vorne considers. “And what guarantees this? Starfleet's word has failed others before.”",
    options: [
      { label: "“I pledge Federation aid and a joint settlement charter.”", goto: "WIN" },
      { label: "“First, power down your weapons — then we'll talk terms.”", goto: "distrust" },
    ],
  },
  hostile: {
    text: "“So. Force it is.” The Rakelli raise shields and the channel cuts. Diplomacy has failed before it began.",
    options: [{ label: "Continue", goto: "LOSE" }],
  },
  tooFast: {
    text: "“An offer with no understanding behind it,” Vorne scoffs. “You do not even know what we need. We do not trust empty generosity.” The talks stall.",
    options: [
      { label: "“Then tell me — what do you need?”", goto: "listen" },
      { label: "“Take the offer or leave.”", goto: "LOSE" },
    ],
  },
  dismiss: {
    text: "“Heartless,” Vorne snaps. “We will not beg.” The fleet moves to take the world by force.",
    options: [{ label: "Continue", goto: "LOSE" }],
  },
  distrust: {
    text: "“You ask us to disarm and trust to hope?” Vorne's patience breaks. “No.” The channel goes dark.",
    options: [{ label: "Continue", goto: "LOSE" }],
  },
};

// The finale fight (tougher than Stage 1, same engine).
const FINALE_BATTLE = {
  playerHP: 22,
  enemyHP: 26,
  enemyName: "Rakelli warship",
  enemyScript: ["attack", "charge", "heavy", "attack", "attack", "charge", "heavy"],
};

export function create(ctx) {
  const { overlay, state, goStage, setStatus } = ctx;
  setStatus("Stage 3 — The Colony Dispute", "Reason with them, or defend the world by force.");

  // Scene: the Enterprise faces the rival fleet over the target world.
  const world = getLayer("world");
  const planet = makeSprite("planet_trappist_e", "planet", "TRAPPIST-1e");
  planet.x = WIDTH * 0.5;
  planet.y = HEIGHT * 0.72;
  planet.scale.set(1.4);
  const ship = makeSprite("enterprise", "ship", "Enterprise");
  ship.x = WIDTH * 0.24; ship.y = HEIGHT * 0.34; ship.scale.set(1.1);
  const enemy = makeSprite("rakelli", "enemy", "Rakelli");
  enemy.x = WIDTH * 0.76; enemy.y = HEIGHT * 0.34; enemy.scale.set(1.1);
  world.addChild(planet, ship, enemy);

  showChoice();

  // ---- The opening fork: diplomacy or fight. ----
  function showChoice() {
    const box = panel("Rival Fleet Detected", "finale-choice");
    box.append(el("p", { text: "A Rakelli colony fleet is moving to claim the world you found. How do you respond?" }));
    box.append(
      el("button", { class: "big-btn", onclick: startDiplomacy }, "🕊️ Open a channel — negotiate"),
      el("button", { class: "big-btn", onclick: startFight }, "⚔️ Raise shields — defend the world")
    );
    overlay.replaceChildren(box);
  }

  // ---- Diplomacy path: walk the dialogue tree. ----
  function startDiplomacy() {
    state.path = "DIPLOMACY";
    renderNode("start");
  }

  function renderNode(nodeId) {
    if (nodeId === "WIN" || nodeId === "LOSE") {
      state.outcome = nodeId;
      goStage(STAGES.ENDING);
      return;
    }
    const node = DIALOGUE[nodeId];
    const box = panel("Negotiation", "dialogue");
    box.append(el("p", { class: "dialogue-text", text: node.text }));
    for (const opt of node.options) {
      box.append(el("button", { class: "big-btn dialogue-opt", onclick: () => renderNode(opt.goto) }, opt.label));
    }
    overlay.replaceChildren(box);
  }

  // ---- Fight path: reuse the Stage 1 card engine with a tougher config. ----
  function startFight() {
    state.path = "FIGHT";
    const battle = createBattle(FINALE_BATTLE);

    const enemyBar = bar(FINALE_BATTLE.enemyName, "enemy");
    const playerBar = bar("Enterprise", "friendly");
    const logEl = el("div", { class: "battle-log" });
    const handEl = el("div", { class: "card-hand" });
    const box = panel("Defend the World", "battle-panel");
    box.append(enemyBar.root, playerBar.root, logEl, handEl);
    overlay.replaceChildren(box);

    function refresh() {
      enemyBar.set(battle.state.enemyHP / battle.state.enemyMaxHP, `${battle.state.enemyHP}/${battle.state.enemyMaxHP}`);
      playerBar.set(battle.state.playerHP / battle.state.playerMaxHP, `${battle.state.playerHP}/${battle.state.playerMaxHP}`);
    }
    function log(line, side) {
      logEl.append(el("div", { class: `log-line ${side}`, text: line }));
      logEl.scrollTop = logEl.scrollHeight;
    }
    function flash(sprite) { sprite.tint = 0xff5555; setTimeout(() => (sprite.tint = 0xffffff), 200); }

    function renderHand() {
      handEl.replaceChildren();
      for (const id of ["phaser", "torpedo", "shield", "evade"]) {
        const card = CARDS[id];
        const usable = battle.canUse(id);
        const btn = el("button", { class: `card card-${card.type}${usable ? "" : " disabled"}`, onclick: usable ? () => onPlay(id) : undefined },
          [el("div", { class: "card-name", text: card.name }), el("div", { class: "card-text", text: card.text })]);
        if (!usable) btn.disabled = true;
        handEl.append(btn);
      }
    }
    function onPlay(id) {
      for (const e of battle.playCard(id)) {
        log(e.text, e.side);
        if (e.side === "player" && e.card && CARDS[e.card].damage) flash(enemy);
        if (e.side === "enemy" && !/dodge|charging/.test(e.text)) flash(ship);
      }
      refresh();
      if (battle.state.over) {
        state.outcome = battle.state.result;
        handEl.replaceChildren(el("button", { class: "big-btn", onclick: () => goStage(STAGES.ENDING) }, "Continue →"));
      } else {
        renderHand();
      }
    }

    log("The Rakelli warship opens fire. Return fire!");
    refresh();
    renderHand();
  }

  return { unmount() {} };
}
