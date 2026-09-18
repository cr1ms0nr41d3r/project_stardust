// static/js/cardBattle.js
// ---------------------------------------------------------------------------
// The CARD BATTLE engine. Pure game logic -- no drawing, no Pixi, no DOM. A UI
// (stage1.js for the tutorial, stage3.js for the finale) calls these functions
// and paints the returned state however it likes.
//
// It is DETERMINISTIC on purpose: there is no randomness. The enemy simply
// follows a fixed script of moves, so the same cards played in the same order
// always give the same result. That makes it easy to learn and easy to test.
//
// One round = the player plays ONE card, then the enemy takes its scripted turn.
// ---------------------------------------------------------------------------

// The four cards the player can play. `type` is just for colour-coding in the UI.
export const CARDS = {
  phaser: { id: "phaser", name: "Phaser", type: "attack", damage: 3, text: "Deal 3 damage." },
  torpedo: { id: "torpedo", name: "Torpedo", type: "attack", damage: 6, cooldown: 2, text: "Deal 6 damage. Recharges every other turn." },
  shield: { id: "shield", name: "Shields", type: "defend", block: 4, text: "Absorb up to 4 damage next enemy turn." },
  evade: { id: "evade", name: "Evade", type: "defend", evade: true, text: "Dodge the enemy's next attack completely." },
};

// What each scripted enemy move does. "charge" deals no damage but powers up the
// NEXT attack (telegraphed, so the player can Evade/Shield in time).
const ENEMY_MOVES = {
  attack: { damage: 4, label: "attacks" },
  heavy: { damage: 7, label: "hits hard" },
  charge: { damage: 0, label: "is charging a heavy blast", charges: true },
};

// Create a battle. `config` lets Stage 3 make a tougher fight with the SAME engine:
//   { playerHP, enemyHP, enemyName, enemyScript: ["attack","charge","heavy", ...] }
export function createBattle(config) {
  const state = {
    playerHP: config.playerHP ?? 20,
    playerMaxHP: config.playerHP ?? 20,
    enemyHP: config.enemyHP ?? 15,
    enemyMaxHP: config.enemyHP ?? 15,
    enemyName: config.enemyName ?? "Hostile ship",
    enemyScript: config.enemyScript ?? ["attack", "attack", "charge", "heavy"],
    enemyIndex: 0,
    shield: 0, // absorbs the next enemy hit
    evade: false, // fully negates the next enemy hit
    charged: false, // set by a "charge" move -> next enemy hit is a "heavy"
    torpedoCd: 0, // turns until Torpedo can be used again (0 = ready)
    turn: 1,
    over: false,
    result: null, // "WIN" | "LOSE"
  };

  // Can this card be played right now? (Only Torpedo has a restriction.)
  function canUse(cardId) {
    if (state.over) return false;
    if (cardId === "torpedo") return state.torpedoCd === 0;
    return !!CARDS[cardId];
  }

  // Play one card, then run the enemy's turn. Returns a list of short log lines
  // describing what happened (the UI prints these and animates from them).
  function playCard(cardId) {
    if (!canUse(cardId)) return [];
    const card = CARDS[cardId];
    const log = [];

    // --- Player's action ---
    if (card.damage) {
      state.enemyHP = Math.max(0, state.enemyHP - card.damage);
      log.push({ side: "player", card: cardId, text: `You fire ${card.name} — ${card.damage} damage.` });
    }
    if (card.block) {
      state.shield = card.block;
      log.push({ side: "player", card: cardId, text: `Shields up — absorbing ${card.block} damage.` });
    }
    if (card.evade) {
      state.evade = true;
      log.push({ side: "player", card: cardId, text: `Evasive maneuvers — the next attack will miss.` });
    }
    if (cardId === "torpedo") state.torpedoCd = card.cooldown;

    // Did that finish the enemy?
    if (state.enemyHP <= 0) {
      state.over = true;
      state.result = "WIN";
      log.push({ side: "system", text: `${state.enemyName} is disabled. You win!` });
      return log;
    }

    // --- Enemy's scripted turn ---
    let moveName = state.enemyScript[state.enemyIndex % state.enemyScript.length];
    // A charged-up enemy upgrades its next attack into a heavy blast.
    if (state.charged && moveName === "attack") moveName = "heavy";
    const move = ENEMY_MOVES[moveName] || ENEMY_MOVES.attack;

    if (move.charges) {
      state.charged = true;
      log.push({ side: "enemy", move: moveName, text: `${state.enemyName} ${move.label}…` });
    } else {
      state.charged = false;
      let incoming = move.damage;
      if (state.evade) {
        log.push({ side: "enemy", move: moveName, text: `${state.enemyName} ${move.label}, but you dodge it!` });
        incoming = 0;
      } else if (state.shield > 0) {
        const absorbed = Math.min(state.shield, incoming);
        incoming -= absorbed;
        log.push({ side: "enemy", move: moveName, text: `${state.enemyName} ${move.label} — shields absorb ${absorbed}, ${incoming} gets through.` });
      } else {
        log.push({ side: "enemy", move: moveName, text: `${state.enemyName} ${move.label} — ${incoming} damage.` });
      }
      state.playerHP = Math.max(0, state.playerHP - incoming);
    }

    // Defences last one turn only.
    state.shield = 0;
    state.evade = false;
    state.enemyIndex++;
    if (state.torpedoCd > 0) state.torpedoCd--;
    state.turn++;

    // Did the enemy finish us?
    if (state.playerHP <= 0) {
      state.over = true;
      state.result = "LOSE";
      log.push({ side: "system", text: `The Enterprise is crippled. You lose.` });
    }

    return log;
  }

  return {
    state,
    canUse,
    playCard,
  };
}
