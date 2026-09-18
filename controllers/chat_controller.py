from pathlib import Path

from models.chat import ChatRequest, ChatResponse
from tools.gemini import ask_gemini_with_tools
from tools.knowledge import build_planet_context
from tools.ship_tools import declarations_for, handlers_for

# A "system instruction" is a standing message the LLM reads before every
# conversation -- it sets the bot's tone and rules. We keep ours in the
# *_personality.md files so a character can be edited without touching code.

# ---------------------------------------------------------------------------
# The CAST of the game. Each crew member maps to:
#   - the personality file that becomes their system instruction, and
#   - the list of tools (from tools/ship_tools.py) they are allowed to use.
#
# Design rule:
#   - Kirk and Spock are people you CONVERSE with. They have NO tools -- they
#     can only talk (e.g. describe the ship's functionality). An empty tool
#     list means Gemini can only reply in words.
#   - The ship's Computer is what actually OPERATES the ship, so it gets every
#     action: raise shields, fire on enemies, scan, go to warp, sound alerts.
# ---------------------------------------------------------------------------
#
# Each crew member now also has a "knowledge" file: an away-mission LENS that
# gives them a distinct skill/knowledge angle for the Stage 2 planet survey
# (Kirk weighs risk to people, Spock analyses the science, the Computer reports
# raw data). This is layered on top of their personality for that stage.
# ---------------------------------------------------------------------------
#
# Every crew member also gets the `lookup_exoplanet` tool so, during the Stage 2
# survey, they can query NASA's real Exoplanet Archive live to fetch precise
# figures for a world (see tools/nasa.py). This is the crew's "access to the
# API" -- the same live source the rest of Stage 2 uses.
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


def run_agent_turn(
    character: str, message: str, planet: str | None = None
) -> tuple[str, list[dict]]:
    """The core game step: talk to one crew member and see what they do.

    `planet` is the id of the world the player is currently surveying in Stage 2
    (or None outside Stage 2). When given, we inject that planet's facts so the
    crew can answer in-context -- without revealing which world is the answer.

    Returns (spoken_reply, ui_events). `ui_events` is the list of things the
    browser should animate (empty if the character only talked).
    """
    profile = CAST.get(character)
    if profile is None:
        # Unknown crew member -> a friendly error instead of a crash.
        return (f"There is no crew member called '{character}' aboard.", [])

    # Build the system instruction in three layers:
    #   personality  -> WHO they are (voice/tone)          [always]
    #   knowledge    -> their away-mission skill lens        [always]
    #   planet_ctx   -> facts about the planet being viewed  [Stage 2 only]
    personality = Path(profile["personality"]).read_text(encoding="utf-8")
    lens = Path(profile["knowledge"]).read_text(encoding="utf-8")
    planet_ctx = build_planet_context(planet, character)
    system_instruction = f"{personality}\n\n{lens}{planet_ctx}"

    # Hand this character ONLY their own tools, then let Gemini decide whether
    # to use one. (See tools/gemini.py for the ask -> act -> narrate loop.)
    reply, events = ask_gemini_with_tools(
        message=message,
        personality=system_instruction,
        declarations=declarations_for(profile["tools"]),
        handlers=handlers_for(profile["tools"]),
    )
    return reply, events


# ---------------------------------------------------------------------------
# The original plain-text endpoints still work (handy for /docs testing). They
# just ignore the UI events and return the spoken reply as before.
# ---------------------------------------------------------------------------

def speak_to_scribe(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    reply, _events = run_agent_turn("scribe", req.message)
    return ChatResponse(reply=reply)

def speak_to_captain(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    reply, _events = run_agent_turn("captain", req.message)
    return ChatResponse(reply=reply)

def speak_to_ship(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    reply, _events = run_agent_turn("ship", req.message)
    return ChatResponse(reply=reply)

def speak_to_navigator(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    reply, _events = run_agent_turn("navigator", req.message)
    return ChatResponse(reply=reply)

def speak_to_chef(req: ChatRequest) -> ChatResponse:
    """Take a validated request, ask the LLM, return a validated response."""
    reply, _events = run_agent_turn("chef", req.message)
    return ChatResponse(reply=reply)
