# tools/gemini.py
# ---------------------------------------------------------------------------
# TOOLS are the helpers that talk to the outside world. This one is our line
# to Gemini, Google's LLM (Large Language Model): give it text, it returns text.
#
# Keeping it here means the rest of the app never needs to know *how* we reach
# the LLM -- it just calls `ask_gemini(...)`.
# ---------------------------------------------------------------------------

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load variables from the .env file (e.g. GEMINI_API_KEY) into the environment.
# This keeps secrets out of the code. Get a free key at:
# https://aistudio.google.com/apikey
load_dotenv()

# The "client" is our phone line to Gemini; the API key proves we may call.
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# "flash" is small, fast, and cheap -> great for learning.
MODEL = "gemini-2.5-flash"
    
# Common gemini calling function    

def ask_gemini(message: str, personality: str) -> str:
    """Send the user's message to Gemini and return its text reply."""
    result = client.models.generate_content(
        model=MODEL,
        contents=message,
        # `config` carries extra settings -- here, the bot's personality.
        config=types.GenerateContentConfig(
            system_instruction=personality,
        ),
    )
    return result.text
