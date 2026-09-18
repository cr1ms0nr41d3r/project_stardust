# tools/ship_tools.py
# ---------------------------------------------------------------------------
# SHIP TOOLS are the "things a crew member can DO" in our role-playing game.
#
# In the world of LLMs, a "tool" (a.k.a. "function calling") is a named action
# we DESCRIBE to the model. The model can't run code itself -- instead, when it
# decides an action fits the user's request, it replies "please call fire_phaser
# with target='Klingon ship'". OUR code then actually runs that action.
#
# So each tool below has TWO halves:
#   1. a DECLARATION  -> the description we hand to Gemini so it knows the tool
#                        exists, what it does, and what arguments it takes.
#   2. a HANDLER      -> the Python function WE run when Gemini asks for it.
#                        Here, the handler's job is to produce a "UI event":
#                        a small dict telling the browser what to animate
#                        (e.g. draw a phaser beam), plus a "result" string that
#                        we feed back to Gemini so the character can narrate it.
#
# The chain the user asked for is:   UI  <->  tool  <->  LLM agent
#   user types "shoot a laser"  ->  Gemini calls fire_phaser  ->  handler makes
#   an event  ->  browser draws the beam AND the captain describes the shot.
# ---------------------------------------------------------------------------

from google.genai import types

from tools.nasa import lookup_exoplanet


# ---------------------------------------------------------------------------
# The HANDLERS.
# Each takes the arguments Gemini chose and returns a UI event dict shaped like:
#   {
#     "action": "<name the browser switches on to pick an animation>",
#     "args":   {<echo of the arguments, for the on-screen log>},
#     "result": "<short sentence fed back to the LLM to narrate>",
#   }
# We keep them tiny and pure (no printing, no network) so they are easy to test.
# ---------------------------------------------------------------------------

def _fire_phaser(args: dict) -> dict:
    target = args.get("target") or "the target"
    return {
        "action": "fire_phaser",
        "args": {"target": target},
        "result": f"Phasers fired at {target}. Direct hit confirmed.",
    }


def _launch_torpedo(args: dict) -> dict:
    target = args.get("target") or "the target"
    return {
        "action": "launch_torpedo",
        "args": {"target": target},
        "result": f"Photon torpedo away, tracking toward {target}. Impact imminent.",
    }


def _raise_shields(args: dict) -> dict:
    # A boolean-ish argument: are we raising (True) or lowering (False) shields?
    up = bool(args.get("up", True))
    return {
        "action": "raise_shields",
        "args": {"up": up},
        "result": "Deflector shields raised to full." if up
        else "Deflector shields lowered.",
    }


def _scan_sensors(args: dict) -> dict:
    target = args.get("target") or "the surrounding area"
    return {
        "action": "scan_sensors",
        "args": {"target": target},
        "result": f"Sensor sweep of {target} complete. Readings displayed on the viewscreen.",
    }


def _set_warp_speed(args: dict) -> dict:
    # Gemini gives us a number; clamp it to the believable warp range 1-9.
    factor = args.get("factor", 5)
    try:
        factor = max(1, min(9, int(factor)))
    except (TypeError, ValueError):
        factor = 5
    return {
        "action": "set_warp_speed",
        "args": {"factor": factor},
        "result": f"Engaging warp {factor}. The stars are streaking past the viewscreen.",
    }


def _red_alert(args: dict) -> dict:
    active = bool(args.get("active", True))
    return {
        "action": "red_alert",
        "args": {"active": active},
        "result": "Red alert! All hands to battle stations." if active
        else "Standing down from red alert. Condition green.",
    }


# ---------------------------------------------------------------------------
# The REGISTRY: one entry per tool, tying the three pieces together.
#   - "declaration": what Gemini is told about the tool.
#   - "handler":     the Python function above that actually runs it.
# `types.Schema` describes the arguments in the shape Gemini expects (a small
# JSON-schema). `types.Type.STRING`/`NUMBER`/`BOOLEAN` name the argument types.
# ---------------------------------------------------------------------------


"""
We want to get a so from this function so that it passes through that exact output as a payload
into out frontend java script to execute a visual function (e.g. firing a laser)!
{
    "target": "the klingon ship"
}
"""


TOOLS: dict[str, dict] = {
    "fire_phaser": {
        "handler": _fire_phaser,
        "declaration": types.FunctionDeclaration(
            name="fire_phaser",
            description="Fire the ship's phasers at a target. Use when the crew "
            "wants to shoot, blast, or open fire with phasers/lasers.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "target": types.Schema(
                        type=types.Type.STRING,
                        description="What to fire at, e.g. 'the Klingon ship'.",
                    ),
                },
            ),
        ),
    },
    "launch_torpedo": {
        "handler": _launch_torpedo,
        "declaration": types.FunctionDeclaration(
            name="launch_torpedo",
            description="Launch a photon torpedo at a target. Use for torpedoes "
            "or a heavier attack than phasers.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "target": types.Schema(
                        type=types.Type.STRING,
                        description="What to launch the torpedo at.",
                    ),
                },
            ),
        ),
    },
    "raise_shields": {
        "handler": _raise_shields,
        "declaration": types.FunctionDeclaration(
            name="raise_shields",
            description="Raise or lower the ship's deflector shields. Use when "
            "the crew wants to defend, protect, or drop the shields.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "up": types.Schema(
                        type=types.Type.BOOLEAN,
                        description="True to raise shields, False to lower them.",
                    ),
                },
            ),
        ),
    },
    "scan_sensors": {
        "handler": _scan_sensors,
        "declaration": types.FunctionDeclaration(
            name="scan_sensors",
            description="Run a sensor sweep/scan of a target or the area. Use for "
            "analysing, scanning, or gathering readings.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "target": types.Schema(
                        type=types.Type.STRING,
                        description="What to scan, e.g. 'the nearby planet'.",
                    ),
                },
            ),
        ),
    },
    "set_warp_speed": {
        "handler": _set_warp_speed,
        "declaration": types.FunctionDeclaration(
            name="set_warp_speed",
            description="Engage warp drive at a given speed (1-9). Use when the "
            "crew wants to fly, travel, jump to warp, or 'engage'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "factor": types.Schema(
                        type=types.Type.NUMBER,
                        description="Warp factor from 1 (slow) to 9 (maximum).",
                    ),
                },
            ),
        ),
    },
    "red_alert": {
        "handler": _red_alert,
        "declaration": types.FunctionDeclaration(
            name="red_alert",
            description="Turn the ship's red alert (battle stations) on or off.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "active": types.Schema(
                        type=types.Type.BOOLEAN,
                        description="True to sound red alert, False to stand down.",
                    ),
                },
            ),
        ),
    },
    "lookup_exoplanet": {
        "handler": lookup_exoplanet,
        "declaration": types.FunctionDeclaration(
            name="lookup_exoplanet",
            description="Look up a confirmed exoplanet in the NASA Exoplanet "
            "Archive by name. Use when the crew wants live figures for a world.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(
                        type=types.Type.STRING,
                        description="Planet name, e.g. 'TRAPPIST-1 e'.",
                    ),
                },
                required=["name"],
            ),
        ),
    },
}


def declarations_for(names: list[str]) -> list[types.FunctionDeclaration]:
    """Collect the Gemini declarations for a subset of tools (by name)."""
    return [TOOLS[name]["declaration"] for name in names if name in TOOLS]


def handlers_for(names: list[str]) -> dict:
    """Collect the Python handlers for a subset of tools, keyed by tool name."""
    return {name: TOOLS[name]["handler"] for name in names if name in TOOLS}
