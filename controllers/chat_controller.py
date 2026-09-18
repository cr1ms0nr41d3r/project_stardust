from pathlib import Path

from models.chat import ChatRequest, ChatResponse
from tools.gemini import ask_gemini_with_tools
from tools.knowledge import build_planet_context
from tools.ship_tools import declarations_for, handlers_for

# Resolve files from the project root so the server works no matter which
# directory uvicorn was started from.
_ROOT = Path(__file__).resolve().parent.parent

# Incoming aliases from older REST routes / docs examples.
_ALIASES = {
    "kirk": "kirk",
    "captain": "kirk",
    "spock": "spock",
    "scribe": "spock",
    "ship": "ship",
    "computer": "ship",
}

# ---------------------------------------------------------------------------
# The CAST of the game. Each crew member maps to:
#   - the personality file that becomes their system instruction, and
#   - the list of tools (from tools/ship_tools.py) they are allowed to use.
#
# Design rule:
#   - Kirk and Spock converse. They only get the NASA lookup tool.
#   - The ship's Computer operates the ship, so it gets every action.
# ---------------------------------------------------------------------------
CAST: dict[str, dict] = {
    "kirk": {
        "personality": "kirk_personality.md",
        "knowledge": "knowledge/kirk_knowledge.md",
        "tools": ["lookup_exoplanet"],
    },
    "spock": {
        "personality": "spocks_personality.md",
        "knowledge": "knowledge/spock_knowledge.md",
        "tools": ["lookup_exoplanet"],
    },
    "ship": {
        "personality": "ships_personality.md",
        "knowledge": "knowledge/computer_knowledge.md",
        "tools": [
            "fire_phaser",
            "launch_torpedo",
            "raise_shields",
            "scan_sensors",
            "set_warp_speed",
            "red_alert",
            "lookup_exoplanet",
        ],
    },
}


def normalize_character(name: str | None) -> str | None:
    """Map display / legacy names onto a CAST key, or None if unknown."""
    if not name:
        return None
    return _ALIASES.get(str(name).strip().lower())


def _read_prompt(rel: str) -> str:
    """Read a markdown prompt, dropping the student-facing header above ---."""
    text = (_ROOT / rel).read_text(encoding="utf-8")
    marker = "\n---\n"
    if marker in text:
        text = text.split(marker, 1)[1]
    return text.strip()


def run_agent_turn(
    character: str,
    message: str,
    planet: str | None = None,
    history: list | None = None,
) -> tuple[str, list[dict]]:
    """The core game step: talk to one crew member and see what they do.

    `planet` is the id of the world the player is currently surveying in Stage 2
    (or None outside Stage 2). When given, we inject that planet's facts so the
    crew can answer in-context -- without revealing which world is the answer.

    `history` is an optional list of prior {role, text} turns for this crew
    member on this connection (short-term memory only).

    Returns (spoken_reply, ui_events).
    """
    key = normalize_character(character) or (character or "").strip().lower()
    profile = CAST.get(key)
    if profile is None:
        return (f"There is no crew member called '{character}' aboard.", [])

    personality = _read_prompt(profile["personality"])
    lens = _read_prompt(profile["knowledge"]) if profile.get("knowledge") else ""
    planet_ctx = build_planet_context(planet, key)
    system_instruction = f"{personality}\n\n{lens}{planet_ctx}"

    reply, events = ask_gemini_with_tools(
        message=message,
        personality=system_instruction,
        declarations=declarations_for(profile["tools"]),
        handlers=handlers_for(profile["tools"]),
        history=history,
    )
    return reply, events


def speak_to_scribe(req: ChatRequest) -> ChatResponse:
    reply, _events = run_agent_turn("spock", req.message)
    return ChatResponse(reply=reply)

def speak_to_captain(req: ChatRequest) -> ChatResponse:
    reply, _events = run_agent_turn("kirk", req.message)
    return ChatResponse(reply=reply)

def speak_to_ship(req: ChatRequest) -> ChatResponse:
    reply, _events = run_agent_turn("ship", req.message)
    return ChatResponse(reply=reply)

def speak_to_navigator(req: ChatRequest) -> ChatResponse:
    reply, _events = run_agent_turn("navigator", req.message)
    return ChatResponse(reply=reply)

def speak_to_chef(req: ChatRequest) -> ChatResponse:
    reply, _events = run_agent_turn("chef", req.message)
    return ChatResponse(reply=reply)
