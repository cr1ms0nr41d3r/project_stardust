# main.py
# ---------------------------------------------------------------------------
# This is the entry point. Its only job is to WIRE THE PIECES TOGETHER.
#
# The app is split into layers, each in its own folder:
#   models/      -> the shape of our data (Pydantic)        e.g. ChatRequest
#   tools/       -> helpers that talk to the outside world  e.g. the LLM client
#   controllers/ -> the business logic ("what should happen")
#   routers/     -> map URLs to controller functions (the web layer)
#
# A request flows: router -> controller -> tool -> back out as a response.
#
# The GAME itself is a browser front-end in `static/` (PixiJS sprites + plain
# JS). This server mainly serves those files; the only live back-end feature is
# the Stage 2 crew chat over the WebSocket (see routers/chat_router.py). Planet
# facts for the crew are loaded by tools/knowledge.py from tools/nasa.py.
# See README.md for the full picture.
# ---------------------------------------------------------------------------

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers.chat_router import router

# Load .env once at boot so GEMINI_API_KEY / NASA_API_KEY are available
# even before the first Gemini call (e.g. GET /planets uses NASA).
load_dotenv()

# `app` is our FastAPI server. We attach the router's endpoints to it.
app = FastAPI(title="Star Trek Bridge")
app.include_router(router)

# The game's front-end lives in the `static/` folder (HTML, CSS, JS). We expose
# that whole folder at the "/static" URL so the browser can load style.css and
# app.js, and we serve the page itself (index.html) at the root "/".
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def play():
    """Serve the bridge UI -- open http://127.0.0.1:8000/ to play."""
    return FileResponse(STATIC_DIR / "index.html")


# Lets the file be started directly with `python main.py`.
# (The usual way is: uvicorn main:app --reload)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
