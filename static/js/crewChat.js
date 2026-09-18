// static/js/crewChat.js
// ---------------------------------------------------------------------------
// The CREW CHAT transport. This is the ONLY part of the game that talks to the
// server: it opens the existing WebSocket at /ws and relays messages both ways.
//
// (This replaces the old static/app.js, keeping its WebSocket handling but
// leaving all the on-screen rendering to stage2.js.)
//
// Protocol (unchanged from the original app):
//   browser -> server : { character, message, planet }   (planet is new/optional)
//   server -> browser : { type: "reply",  character, text }
//                       { type: "action", action, args }   (we just surface these)
// ---------------------------------------------------------------------------

export function createCrewChat({ onReply, onAction, onStatus }) {
  const wsProtocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${wsProtocol}://${location.host}/ws`);

  socket.addEventListener("open", () => onStatus && onStatus("connected"));
  socket.addEventListener("close", () => onStatus && onStatus("closed"));
  socket.addEventListener("error", () => onStatus && onStatus("error"));

  socket.addEventListener("message", (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      return;
    }
    if (data.type === "action" && onAction) onAction(data);
    else if (data.type === "reply" && onReply) onReply(data);
  });

  return {
    // Send the player's line for a given crew member, with the planet they're
    // currently looking at so the crew can answer in-context.
    send(character, message, planet) {
      if (socket.readyState !== WebSocket.OPEN) return false;
      socket.send(JSON.stringify({ character, message, planet: planet || null }));
      return true;
    },
    isOpen() {
      return socket.readyState === WebSocket.OPEN;
    },
    close() {
      try {
        socket.close();
      } catch {
        /* already closing */
      }
    },
  };
}
