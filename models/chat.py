# models/chat.py
# ---------------------------------------------------------------------------
# MODELS describe the SHAPE of our data: what fields exist and their types.
#
# What is Pydantic?
#   Pydantic is a library that turns a plain Python class into a strict data
#   checker. You declare the fields you expect (and their types), and Pydantic
#   guarantees any data it builds matches that declaration -- or raises a clear
#   error. FastAPI uses these models to automatically read, validate, and
#   document the JSON going in and out of our endpoints. No manual `if`-checks.
#
# A class that inherits from `BaseModel` IS a Pydantic model.
# ---------------------------------------------------------------------------

from pydantic import BaseModel


# Incoming data: the request body must contain a "message" string.
# If the caller sends a number, or forgets the field, Pydantic rejects it.
class ChatRequest(BaseModel):
    message: str


# Outgoing data: what we send back -- a single "reply" string.
class ChatResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Models for the real-time game over the WebSocket.
#
# A WebSocket is a two-way pipe kept open between browser and server, so either
# side can send messages at any time (unlike a normal request/response). We use
# it so an ACTION (drawing a phaser beam) and the character's SPOKEN reply can
# arrive as separate, live events.
# ---------------------------------------------------------------------------

# Server -> browser: one UI event = one thing to animate on the viewscreen.
# (Sent whenever a tool the LLM called wants the screen to react.)
class GameEvent(BaseModel):
    type: str = "action"      # tells the browser this is an animation cue
    action: str               # e.g. "fire_phaser" -> which animation to play
    args: dict = {}           # details, e.g. {"target": "the Klingon ship"}


# Server -> browser: the character's spoken line (shown in the chat log).
class GameReply(BaseModel):
    type: str = "reply"
    character: str
    text: str
