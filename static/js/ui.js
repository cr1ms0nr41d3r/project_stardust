// static/js/ui.js
// ---------------------------------------------------------------------------
// Tiny helpers for building the HTML overlay (buttons, panels, text). Nothing
// clever -- just less typing than document.createElement everywhere. The look
// of everything created here comes from the LCARS classes in style.css.
// ---------------------------------------------------------------------------

// el("button", { class: "btn", onclick: fn }, "Label")
//   - props: attributes; special keys `onclick`/`class`/`html`/`text`.
//   - children: a string, a node, or an array of them.
export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else if (key === "onclick") node.addEventListener("click", value);
    else if (key === "html") node.innerHTML = value;
    else if (key === "text") node.textContent = value;
    else if (value != null) node.setAttribute(key, value);
  }
  const kids = Array.isArray(children) ? children : [children];
  for (const kid of kids) {
    if (kid == null) continue;
    node.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return node;
}

// A framed LCARS panel with an optional title. Returns the panel element.
export function panel(title, className = "") {
  const p = el("div", { class: `panel ${className}`.trim() });
  if (title) p.append(el("div", { class: "panel-title", text: title }));
  return p;
}

// A simple horizontal bar (used for HP). Returns { root, set(fraction) }.
export function bar(label, colorClass = "") {
  const fill = el("div", { class: `bar-fill ${colorClass}`.trim() });
  const root = el("div", { class: "bar" }, [
    el("div", { class: "bar-label", text: label }),
    el("div", { class: "bar-track" }, fill),
  ]);
  return {
    root,
    set(fraction, text) {
      fill.style.width = `${Math.max(0, Math.min(1, fraction)) * 100}%`;
      if (text != null) fill.setAttribute("data-text", text);
    },
  };
}
