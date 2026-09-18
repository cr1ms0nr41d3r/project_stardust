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
# ---------------------------------------------------------------------------

from fastapi import FastAPI

from routers.chat_router import router

# `app` is our FastAPI server. We attach the router's endpoints to it.
app = FastAPI(title="Gemini Chatbot")
app.include_router(router)


# Lets the file be started directly with `python main.py`.
# (The usual way is: uvicorn main:app --reload)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
