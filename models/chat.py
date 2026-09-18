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
