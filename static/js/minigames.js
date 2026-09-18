// static/js/minigames.js
// ---------------------------------------------------------------------------
// MINI-GAMES: three tiny, reusable templates. Each planet in planets.json picks
// a template and supplies its own `config` (the labels/answers), so we get six
// different-feeling puzzles from three small pieces of code.
//
//   sort      -> put each item in the correct bin (e.g. breathable vs toxic)
//   sequence  -> watch a short pattern, then repeat it in order
//   calibrate -> stop a moving marker inside a target band (timing)
//
// Public API:
//   mountMinigame(container, minigame, { onWin }) -> { destroy() }
// Each template calls onWin() once solved. destroy() stops any animation/timer.
// ---------------------------------------------------------------------------

import { el } from "./ui.js";

export function mountMinigame(container, minigame, { onWin }) {
  const template = MINIGAMES[minigame.template];
  if (!template) {
    container.append(el("div", { text: `Unknown mini-game: ${minigame.template}` }));
    return { destroy() {} };
  }
  return template(container, minigame.config, onWin);
}

const MINIGAMES = { sort, sequence, calibrate };

// ---------------------------------------------------------------------------
// SORT — assign every item to a bin, then Confirm. All correct = win.
// ---------------------------------------------------------------------------
function sort(container, config, onWin) {
  const chosen = {}; // itemLabel -> binName
  container.append(el("p", { class: "mg-prompt", text: config.prompt }));

  const rows = el("div", { class: "mg-sort" });
  for (const item of config.items) {
    const bins = config.bins.map((binName) =>
      el(
        "button",
        {
          class: "mg-bin-btn",
          onclick: () => {
            chosen[item.label] = binName;
            // Highlight the picked bin for this row.
            [...binsWrap.children].forEach((b) => b.classList.toggle("picked", b.textContent === binName));
            confirmBtn.disabled = Object.keys(chosen).length < config.items.length;
          },
        },
        binName
      )
    );
    const binsWrap = el("div", { class: "mg-bins" }, bins);
    rows.append(el("div", { class: "mg-row" }, [el("span", { class: "mg-item", text: item.label }), binsWrap]));
  }
  container.append(rows);

  const feedback = el("div", { class: "mg-feedback" });
  const confirmBtn = el(
    "button",
    {
      class: "big-btn",
      onclick: () => {
        const wrong = config.items.filter((it) => chosen[it.label] !== it.bin);
        if (wrong.length === 0) {
          feedback.textContent = "✔ Correct — analysis complete.";
          onWin();
        } else {
          feedback.textContent = `✘ ${wrong.length} reading(s) misclassified. Adjust and confirm again.`;
        }
      },
    },
    "Confirm analysis"
  );
  confirmBtn.disabled = true;
  container.append(confirmBtn, feedback);

  return { destroy() {} };
}

// ---------------------------------------------------------------------------
// SEQUENCE — show the pattern for a moment, hide it, then the player repeats it
// by clicking the symbol buttons in order.
// ---------------------------------------------------------------------------
function sequence(container, config, onWin) {
  let input = [];
  let revealTimer = null;

  container.append(el("p", { class: "mg-prompt", text: config.prompt }));
  const display = el("div", { class: "mg-seq-display" });
  const feedback = el("div", { class: "mg-feedback" });
  container.append(display);

  const buttons = config.symbols.map((sym) =>
    el("button", { class: "mg-seq-btn", onclick: () => onInput(sym) }, sym)
  );
  const pad = el("div", { class: "mg-seq-pad" }, buttons);

  function reveal() {
    input = [];
    feedback.textContent = "Watch…";
    pad.style.pointerEvents = "none";
    display.textContent = config.pattern.join("   ");
    clearTimeout(revealTimer);
    revealTimer = setTimeout(() => {
      display.textContent = "• • •";
      feedback.textContent = "Now repeat the pattern.";
      pad.style.pointerEvents = "auto";
    }, 1800);
  }

  function onInput(sym) {
    input.push(sym);
    const i = input.length - 1;
    if (config.pattern[i] !== sym) {
      feedback.textContent = "✘ Wrong order — watch again.";
      reveal();
      return;
    }
    if (input.length === config.pattern.length) {
      feedback.textContent = "✔ Pattern matched — scan confirmed.";
      pad.style.pointerEvents = "none";
      onWin();
    }
  }

  container.append(pad, el("button", { class: "link-btn", onclick: reveal }, "↻ Show pattern again"), feedback);
  reveal();

  return {
    destroy() {
      clearTimeout(revealTimer);
    },
  };
}

// ---------------------------------------------------------------------------
// CALIBRATE — a marker slides back and forth across a track; click Stop to lock
// it. Land inside the green target band to win. Pure timing, no randomness.
// ---------------------------------------------------------------------------
function calibrate(container, config, onWin) {
  let pos = 0; // 0..100
  let dir = 1;
  let rafId = null;
  let last = null;
  let stopped = false;

  container.append(el("p", { class: "mg-prompt", text: config.prompt }));

  const band = el("div", { class: "mg-band" });
  band.style.left = `${config.targetMin}%`;
  band.style.width = `${config.targetMax - config.targetMin}%`;
  const marker = el("div", { class: "mg-marker" });
  const track = el("div", { class: "mg-track" }, [band, marker]);
  const feedback = el("div", { class: "mg-feedback" });

  const stopBtn = el("button", { class: "big-btn", onclick: stop }, "■ Stop");
  container.append(track, stopBtn, feedback);

  function frame(now) {
    if (last == null) last = now;
    const dt = now - last;
    last = now;
    pos += dir * (config.speed || 0.12) * dt;
    if (pos >= 100) { pos = 100; dir = -1; }
    if (pos <= 0) { pos = 0; dir = 1; }
    marker.style.left = `${pos}%`;
    if (!stopped) rafId = requestAnimationFrame(frame);
  }
  rafId = requestAnimationFrame(frame);

  function stop() {
    if (stopped) return;
    stopped = true;
    cancelAnimationFrame(rafId);
    if (pos >= config.targetMin && pos <= config.targetMax) {
      feedback.textContent = "✔ Locked on — calibration successful.";
      stopBtn.disabled = true;
      onWin();
    } else {
      feedback.textContent = "✘ Missed the band. Recalibrating…";
      stopBtn.textContent = "■ Stop";
      // Retry: resume sliding after a beat.
      setTimeout(() => {
        stopped = false;
        last = null;
        rafId = requestAnimationFrame(frame);
      }, 600);
    }
  }

  return {
    destroy() {
      stopped = true;
      cancelAnimationFrame(rafId);
    },
  };
}
