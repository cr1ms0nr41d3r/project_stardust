// static/js/state.js
// ---------------------------------------------------------------------------
// The GAME STATE: one plain object that remembers where the player is and what
// they've done. It lives only in memory -- refreshing the page starts over
// (which is exactly what we want for this simple, local game).
//
// The three stages form a state machine. main.js reads/writes this object and
// decides which stage to show next; the stage modules only report their result.
// ---------------------------------------------------------------------------

export const STAGES = {
  BOOT: "BOOT",
  STAGE1: "STAGE1", // card-battle tutorial (no AI)
  STAGE2: "STAGE2", // explore 6 planets, talk to the AI crew, pick the best
  STAGE3: "STAGE3", // enemy colony: diplomacy or fight (no AI)
  ENDING: "ENDING", // win/lose screen -> restart
};

// A fresh, brand-new game. Called at boot and on every restart.
export function newGameState() {
  return {
    stage: STAGES.BOOT,

    // Stage 2 progress. A planet counts as "explored" once its mini-game is won.
    planetsExplored: new Set(), // of planet ids
    chosenPlanetId: null, // the player's final habitable-planet pick

    // Stage 3.
    path: null, // "DIPLOMACY" | "FIGHT"
    outcome: null, // "WIN" | "LOSE"
  };
}
