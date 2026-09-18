// static/js/crewChat.js
// ---------------------------------------------------------------------------
// The CREW CHAT transport. This is the ONLY part of the game that talks to the
// server: it opens the existing WebSocket at /ws and relays messages both ways.
//
// Protocol:
//   browser -> server : { character, message, planet }   (planet is optional)
//   server -> browser : { type: "reply",  character, text }
//                       { type: "action", action, args }
// ---------------------------------------------------------------------------

export function createCrewChat({ onReply, onAction, onStatus }) {
  const wsProtocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${wsProtocol}://${location.host}/ws`);
  let pending = false;

  socket.addEventListener("open", () => onStatus && onStatus("connected"));
  socket.addEventListener("close", () => {
    pending = false;
    onStatus && onStatus("closed");
  });
  socket.addEventListener("error", () => onStatus && onStatus("error"));

  socket.addEventListener("message", (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      return;
    }
    if (data.type === "action" && onAction) onAction(data);
    else if (data.type === "reply") {
      pending = false;
      if (onReply) onReply(data);
    }
  });

  return {
    send(character, message, planet) {
      if (pending || socket.readyState !== WebSocket.OPEN) return false;
      pending = true;
      socket.send(JSON.stringify({ character, message, planet: planet || null }));
      return true;
    },
    isOpen() {
      return socket.readyState === WebSocket.OPEN;
    },
    close() {
      pending = false;
      try {
        socket.close();
      } catch {
        /* already closing */
      }
    },
  };
}
