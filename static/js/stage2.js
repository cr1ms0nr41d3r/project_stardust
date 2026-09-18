// static/js/stage2.js
// ---------------------------------------------------------------------------
// STAGE 2 — planet exploration. This is the ONLY stage that uses the AI crew.
//
// The player surveys six worlds (data in /static/data/planets.json). For each
// planet they can:
//   * read its real habitability FACT,
//   * play a MINI-GAME (winning it marks the planet "explored"),
//   * ASK THE CREW (Kirk / Spock / Computer) about it — answered live by the
//     AI over the WebSocket, each crew member with their own knowledge lens.
//
// Once all six are explored, the player must CHOOSE the most habitable world.
// Exactly one is correct; a correct pick advances to Stage 3, a wrong pick asks
// them to reconsider. The crew never state the answer outright (the backend
// hides the `habitable` flag), so the player has to reason it out.
// ---------------------------------------------------------------------------

import { getLayer, WIDTH, HEIGHT, setBackdrop, clearBackdrop } from "./scene.js";
import { makeSprite } from "./assets.js";
import { mountMinigame } from "./minigames.js";
import { createCrewChat } from "./crewChat.js";
import { STAGES } from "./state.js";
import { el, panel } from "./ui.js";

const CREW = [
  { id: "kirk", name: "Capt. Kirk" },
  { id: "spock", name: "Mr. Spock" },
  { id: "ship", name: "Computer" },
];

export function create(ctx) {
  const { overlay, state, goStage, setStatus } = ctx;
  setStatus("Stage 2 — Survey Mission", "Explore all six worlds, then choose the most habitable.");

  const world = getLayer("world");
  let planets = [];
  let openPlanet = null;
  let minigame = null; // active mini-game handle (to destroy on close)

  // One shared chat connection for the whole stage.
  let chatEnabled = true;
  const chat = createCrewChat({
    onReply: (data) => appendChat(nameFor(data.character), data.text, "crew"),
    // When a crew member uses the NASA lookup tool, surface it so the player can
    // see the real API being queried live.
    onAction: (data) => {
      if (data.action === "nasa_lookup") {
        const target = (data.args && data.args.name) || "the archive";
        appendChat("System", `📡 Queried the NASA Exoplanet Archive for ${target}…`, "system");
      }
    },
    onStatus: (s) => {
      if (s === "closed" || s === "error") {
        chatEnabled = false;
        appendChat("System", "Crew comms offline (no API key?). Facts and mini-games still work.", "system");
      }
    },
  });

  // ---- Root layout: a target list (left) and a detail panel (right). ----
  const list = panel("Survey Targets", "planet-list");
  const detail = panel("Select a world", "planet-detail");
  const chooseBtn = el(
    "button",
    { class: "big-btn choose-btn", onclick: openChooser },
    "Choose the most habitable world →"
  );
  chooseBtn.disabled = true;

  const root = el("div", { class: "stage2" }, [list, detail]);
  overlay.append(root, chooseBtn);

  // ---- Load planet data from the server (built from live NASA data). ----
  fetch("/planets")
    .then((r) => r.json())
    .then((data) => {
      planets = data.planets;
      if (data.backdrop) setBackdrop(data.backdrop); // real NASA APOD image
      drawPlanetBackdrop();
      buildList();
    })
    .catch((err) => {
      detail.append(el("p", { text: `Failed to load planet data: ${err}` }));
    });

  // Decorative: the six worlds arranged across the scene.
  function drawPlanetBackdrop() {
    planets.forEach((p, i) => {
      const sprite = makeSprite(p.sprite, "planet", p.name);
      sprite.x = WIDTH * (0.16 + (i % 3) * 0.34);
      sprite.y = HEIGHT * (0.34 + Math.floor(i / 3) * 0.36);
      sprite.scale.set(0.7);
      world.addChild(sprite);
    });
  }

  function buildList() {
    list.querySelectorAll(".planet-item").forEach((n) => n.remove());
    for (const p of planets) {
      const explored = state.planetsExplored.has(p.id);
      const item = el(
        "button",
        {
          class: `planet-item${explored ? " explored" : ""}${openPlanet === p.id ? " open" : ""}`,
          onclick: () => openDetail(p.id),
        },
        [el("span", { text: p.name }), el("span", { class: "tick", text: explored ? "✓" : "•" })]
      );
      list.append(item);
    }
  }

  function nameFor(id) {
    return (CREW.find((c) => c.id === id) || {}).name || "Crew";
  }

  // ---- Detail panel for one planet: fact + mini-game + crew chat. ----
  let chatLogEl = null;

  function openDetail(id) {
    if (minigame) { minigame.destroy(); minigame = null; }
    openPlanet = id;
    buildList();
    const p = planets.find((x) => x.id === id);

    detail.replaceChildren(el("div", { class: "panel-title", text: p.name }));

    // Fact.
    detail.append(el("p", { class: "planet-fact", text: p.fact }));

    // Science readout (real NASA figures).
    const sci = el("div", { class: "science-grid" });
    for (const [k, v] of Object.entries(p.science)) {
      sci.append(el("div", { class: "sci-cell" }, [el("b", { text: k.replace(/_/g, " ") + ": " }), String(v)]));
    }
    detail.append(sci);

    // Where the data came from.
    const yr = p.disc_year ? ` · discovered ${p.disc_year}` : "";
    detail.append(el("div", { class: "data-source", text: `Source: ${p.source || "NASA Exoplanet Archive"}${yr}` }));

    // Mini-game section.
    const explored = state.planetsExplored.has(id);
    const mgWrap = el("div", { class: "mg-wrap" });
    if (explored) {
      mgWrap.append(el("div", { class: "mg-done", text: "✓ Survey complete for this world." }));
    } else {
      const startBtn = el("button", { class: "big-btn", onclick: () => startMinigame(p, mgWrap) }, "▶ Run survey mini-game");
      mgWrap.append(startBtn);
    }
    detail.append(el("div", { class: "panel-subtitle", text: "Survey" }), mgWrap);

    // Crew chat section.
    detail.append(el("div", { class: "panel-subtitle", text: "Ask the crew" }));
    detail.append(buildChat(p));
  }

  function startMinigame(p, mgWrap) {
    mgWrap.replaceChildren();
    const host = el("div", { class: "mg-host" });
    mgWrap.append(host);
    minigame = mountMinigame(host, p.minigame, {
      onWin: () => {
        state.planetsExplored.add(p.id);
        mgWrap.replaceChildren(el("div", { class: "mg-done", text: "✓ Survey complete for this world." }));
        buildList();
        maybeEnableChoose();
      },
    });
  }

  function maybeEnableChoose() {
    if (state.planetsExplored.size >= planets.length) {
      chooseBtn.disabled = false;
      setStatus("Stage 2 — All worlds surveyed", "Now choose the most habitable world.");
    }
  }

  // ---- The crew chat widget inside the detail panel. ----
  function buildChat(p) {
    const wrap = el("div", { class: "chat" });
    const crewRow = el("div", { class: "crew-row" });
    let active = "spock"; // sensible default for a science question
    const crewBtns = CREW.map((c) =>
      el("button", { class: `crew-btn${c.id === active ? " active" : ""}`, onclick: () => {
        active = c.id;
        [...crewRow.children].forEach((b) => b.classList.toggle("active", b.textContent === c.name));
      }}, c.name)
    );
    crewRow.append(...crewBtns);

    chatLogEl = el("div", { class: "chat-log" });
    const inputEl = el("input", { type: "text", class: "chat-input", placeholder: `Ask about ${p.name}…`, autocomplete: "off" });
    const sendBtn = el("button", { class: "chat-send" }, "Send");

    function submit(e) {
      e && e.preventDefault();
      const text = inputEl.value.trim();
      if (!text) return;
      if (!chatEnabled || !chat.isOpen()) {
        appendChat("System", "Crew comms offline. Use the fact and mini-game instead.", "system");
        return;
      }
      appendChat("You", text, "you");
      chat.send(active, text, openPlanet);
      inputEl.value = "";
    }

    const form = el("form", { class: "chat-form" }, [inputEl, sendBtn]);
    form.addEventListener("submit", submit); // el() only special-cases onclick

    wrap.append(crewRow, chatLogEl, form);
    return wrap;
  }

  function appendChat(who, text, cls) {
    if (!chatLogEl) return;
    chatLogEl.append(el("div", { class: `chat-msg ${cls}` }, [el("b", { text: who + ": " }), text]));
    chatLogEl.scrollTop = chatLogEl.scrollHeight;
  }

  // ---- The final pick. ----
  function openChooser() {
    if (minigame) { minigame.destroy(); minigame = null; }
    const box = panel("Which world is the most habitable?", "chooser");
    const feedback = el("div", { class: "mg-feedback" });
    for (const p of planets) {
      box.append(
        el("button", { class: "big-btn choose-option", onclick: () => grade(p, feedback) }, p.name)
      );
    }
    box.append(feedback);
    detail.replaceChildren();
    detail.append(box);
  }

  function grade(p, feedback) {
    if (p.habitable) {
      state.chosenPlanetId = p.id;
      feedback.textContent = `✔ Correct — ${p.name} is a Class-M world. Setting course.`;
      setTimeout(() => goStage(STAGES.STAGE3, { planetId: p.id }), 1200);
    } else {
      feedback.textContent = `✘ ${p.name} isn't the best choice. Reconsider what habitability really needs.`;
    }
  }

  // Clean up the socket + any running mini-game when leaving the stage.
  return {
    unmount() {
      if (minigame) minigame.destroy();
      chat.close();
      clearBackdrop();
    },
  };
}
