# controllers/chat_controller.py
# ---------------------------------------------------------------------------
# CONTROLLERS hold the business logic: the "what should happen" for a request,
# free of any web-server details. The router (HTTP) calls the controller, and
# the controller uses tools (the LLM) to do the actual work.
#
# This separation means we could swap the web framework or the LLM without
# rewriting the logic that ties them together.
# ---------------------------------------------------------------------------

from pathlib import Path
from models.chat import ChatRequest, ChatResponse
from tools.gemini import ask_gemini

# A "system instruction" is a standing message the LLM reads before every
# conversation -- it sets the bot's tone and rules. We keep ours in
# personality.md so the character can be edited without touching code.

def speak_to_spock(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    spocks_personality = Path("spocks_personality.md").read_text(encoding="utf-8")
    reply = ask_gemini(req.message, spocks_personality)
    return ChatResponse(reply=reply)

def speak_to_kirk(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    kirks_personality = Path("kirk_personality.md").read_text(encoding="utf-8")
    reply = ask_gemini(req.message, kirks_personality)
    return ChatResponse(reply=reply)

def speak_to_ship(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    ships_personality = Path("ships_personality.md").read_text(encoding="utf-8")
    reply = ask_gemini(req.message, ships_personality)
    return ChatResponse(reply=reply)
