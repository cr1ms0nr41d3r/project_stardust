# routers/chat_router.py
# ---------------------------------------------------------------------------
# ROUTERS map URLs to code. An APIRouter is a group of endpoints that we plug
# into the main app. Each function below runs when its URL is requested; the
# real work is delegated to the controller.
# ---------------------------------------------------------------------------

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from controllers.chat_controller import (
    normalize_character,
    run_agent_turn,
    speak_to_captain,
    speak_to_scribe,
    speak_to_ship,
    speak_to_navigator,
    speak_to_chef,
)
from models.chat import ChatRequest, ChatResponse, GameEvent, GameReply

router = APIRouter()

_MAX_MESSAGE = 2000
_HISTORY_TURNS = 8  # user+model pairs kept per crew member on this socket


# Health check: GET http://localhost:8000/health confirms the server is alive.
# (The "/" address now serves the game UI -- see main.py.)
@router.get("/health")
def health():
    return {"status": "ok", "try": "open http://127.0.0.1:8000/ to play"}


# The Stage 2 planets. The browser fetches this instead of a static file so the
# six worlds are built from REAL, LIVE NASA Exoplanet Archive data (with a cache
# + bundled fallback if NASA is unreachable). The api.nasa.gov key stays on the
# server; it is never included in this response.
@router.get("/planets")
def planets():
    from tools import nasa

    return {"planets": nasa.build_planets(), **nasa.get_backdrop()}


# The chat endpoints. FastAPI sees `req: ChatRequest` and automatically reads
# the JSON body, validates it against the model, and hands us a ready `req`.
# `response_model` tells FastAPI (and the docs) the shape we return.


@router.post("/speak_with_captain", response_model=ChatResponse)
def chat_with_captain(req: ChatRequest):
    return speak_to_captain(req)


@router.post("/speak_with_scribe", response_model=ChatResponse)
def chat_with_scribe(req: ChatRequest):
    return speak_to_scribe(req)


@router.post("/speak_with_ship", response_model=ChatResponse)
def chat_with_ship(req: ChatRequest):
    return speak_to_ship(req)


@router.post("/speak_with_navigator", response_model=ChatResponse)
def chat_with_navigator(req: ChatRequest):
    return speak_to_navigator(req)


@router.post("/speak_with_chef", response_model=ChatResponse)
def chat_with_chef(req: ChatRequest):
    return speak_to_chef(req)


# ---------------------------------------------------------------------------
# The WebSocket endpoint -- this is what the game UI connects to.
#
# A WebSocket stays open, so we loop: wait for a message from the browser,
# run the agent turn, then send back (a) any ACTION events for the viewscreen
# and (b) the character's spoken REPLY. Then we wait for the next message.
# ---------------------------------------------------------------------------
@router.websocket("/ws")
async def game_socket(websocket: WebSocket):
    await websocket.accept()  # Complete the handshake; the pipe is now open.
    # Short-term memory for this connection only: {character: [{role, text}, ...]}
    histories: dict[str, list] = {}

    try:
        while True:
            # 1. Wait for the player's message, e.g. {"character": "kirk",
            #    "message": "Is this world too hot for a colony?"}
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                continue

            character = normalize_character(data.get("character"))
            message = str(data.get("message") or "").strip()
            planet = data.get("planet")
            if planet is not None:
                planet = str(planet).strip() or None

            if character is None or not message:
                await websocket.send_json(
                    GameReply(
                        character=str(data.get("character") or "crew"),
                        text="Please choose a crew member and send a short message.",
                    ).model_dump()
                )
                continue
            if len(message) > _MAX_MESSAGE:
                message = message[:_MAX_MESSAGE]

            history = histories.get(character, [])

            # 2. Ask the crew member. The Gemini call is BLOCKING (it waits on
            #    the network), so we run it in a worker thread with
            #    `asyncio.to_thread` -- otherwise it would freeze the server for
            #    every other connection while we wait.
            try:
                reply, events = await asyncio.to_thread(
                    run_agent_turn, character, message, planet, history
                )
            except Exception as exc:  # noqa: BLE001 -- keep the game alive
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    reply = ("Subspace channel congested (API rate limit "
                             "reached). Please wait a moment and try again.")
                else:
                    reply = "Communications error. Please try that again."
                events = []

            histories[character] = (history + [
                {"role": "user", "text": message},
                {"role": "model", "text": reply},
            ])[-_HISTORY_TURNS * 2:]

            # 3. Send each action first so the animation kicks off...
            for event in events:
                await websocket.send_json(
                    GameEvent(
                        action=event.get("action", ""),
                        args=event.get("args") or {},
                    ).model_dump()
                )

            # 4. ...then the spoken line for the chat log.
            await websocket.send_json(
                GameReply(character=character, text=reply).model_dump()
            )
    except WebSocketDisconnect:
        # The player closed the tab -- nothing to clean up, just stop looping.
        pass


