# tools/gemini.py
# ---------------------------------------------------------------------------
# TOOLS are the helpers that talk to the outside world. This one is our line
# to Gemini, Google's LLM (Large Language Model): give it text, it returns text.
#
# Keeping it here means the rest of the app never needs to know *how* we reach
# the LLM -- it just calls `ask_gemini_with_tools(...)`.
# ---------------------------------------------------------------------------

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load variables from the .env file (e.g. GEMINI_API_KEY) into the environment.
# This keeps secrets out of the code. Get a free key at:
# https://aistudio.google.com/apikey
load_dotenv()

# "flash" is small, fast, and cheap -> great for learning.
MODEL = "gemini-2.5-flash"

# The "client" is our phone line to Gemini; the API key proves we may call.
# We build it LAZILY (on first use) instead of at import, so the server can
# start and serve the game even with no key set -- Stages 1 and 3 use no AI at
# all, and Stage 2's chat simply reports a clear error if the key is missing.
_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to a .env file to talk to the "
                "crew in Stage 2. (Stages 1 and 3 work without it.)"
            )
        _client = genai.Client(api_key=key)
    return _client


# ---------------------------------------------------------------------------
# The tool-aware version, used by the role-playing game.
#
# On top of "send text, get text", this also hands Gemini a list of TOOLS it is
# allowed to call (see tools/ship_tools.py). If Gemini decides an action fits,
# it doesn't reply with words -- it replies "call fire_phaser(target=...)". We
# then run our matching handler, feed the result back, and let Gemini narrate.
#
# This back-and-forth is the classic "agent loop":
#   ask -> model wants a tool -> run it -> tell the model the outcome -> repeat
#   until the model is happy to answer in plain words.
# ---------------------------------------------------------------------------

def _response_text(response) -> str:
    """Pull spoken text out of a Gemini response without crashing on blocks."""
    try:
        text = response.text
        if text:
            return text
    except Exception:
        pass
    try:
        parts = response.candidates[0].content.parts or []
        return "".join(getattr(p, "text", None) or "" for p in parts).strip()
    except Exception:
        return ""


def ask_gemini_with_tools(
    message: str,
    personality: str,
    declarations: list,
    handlers: dict,
    history: list | None = None,
) -> tuple[str, list[dict]]:
    """Ask Gemini, letting it call tools. Return (reply_text, ui_events).

    `declarations` are the tool descriptions Gemini may use; `handlers` maps a
    tool name to the Python function that actually performs it. Every performed
    tool produces a UI event, which we collect and return for the browser.
    `history` is optional prior turns: [{"role": "user"|"model", "text": "..."}].
    """
    config = types.GenerateContentConfig(
        system_instruction=personality,
        # Offer the tools. `Tool(function_declarations=[...])` is Gemini's
        # wrapper around our list of tool descriptions.
        tools=[types.Tool(function_declarations=declarations)] if declarations else None,
    )

    # `contents` is the running transcript. Recent history (if any) plus the
    # new user line, then it grows as the model calls tools.
    contents = []
    for turn in history or []:
        role = turn.get("role") or "user"
        text = (turn.get("text") or "").strip()
        if text and role in ("user", "model"):
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    events: list[dict] = []

    client = _get_client()  # builds the client on first call (needs the key)
    response = client.models.generate_content(
        model=MODEL, contents=contents, config=config
    )

    # Keep looping while the model asks for tools. The cap (5) is a safety belt
    # so a confused model can never loop forever.
    for _ in range(5):
        calls = response.function_calls or []
        if not calls:
            break  # No tool requested -> the model is ready to speak.

        # Record the model's "please call these tools" turn in the transcript.
        if not response.candidates:
            break
        contents.append(response.candidates[0].content)

        # Run each requested tool and add its result back to the transcript.
        for call in calls:
            args = dict(call.args) if call.args else {}
            handler = handlers.get(call.name)
            if handler:
                event = handler(args)
            else:
                # The model named a tool we don't have -- fail gracefully.
                event = {
                    "action": call.name,
                    "args": args,
                    "result": "That action is not available on this ship.",
                }
            events.append(event)

            # Hand the tool's outcome back so the model can narrate it. A
            # "function_response" is the mirror image of a "function_call".
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=call.name,
                            response={"result": event["result"]},
                        )
                    ],
                )
            )

        # Ask again now that the model knows what happened.
        response = client.models.generate_content(
            model=MODEL, contents=contents, config=config
        )

    reply = _response_text(response) or "No response from subspace comms."
    return reply, events
