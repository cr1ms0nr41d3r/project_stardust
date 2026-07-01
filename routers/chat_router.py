# routers/chat_router.py
# ---------------------------------------------------------------------------
# ROUTERS map URLs to code. An APIRouter is a group of endpoints that we plug
# into the main app. Each function below runs when its URL is requested; the
# real work is delegated to the controller.
# ---------------------------------------------------------------------------

from fastapi import APIRouter

from controllers.chat_controller import speak_to_spock, speak_to_kirk, speak_to_ship
from models.chat import ChatRequest, ChatResponse

router = APIRouter()


# Health check: GET http://localhost:8000/ confirms the server is alive.
@router.get("/")
def home():
    return {"status": "ok", "try": "POST /chat with {\"message\": \"hi\"}"}


# The chat endpoint. FastAPI sees `req: ChatRequest` and automatically reads
# the JSON body, validates it against the model, and hands us a ready `req`.
# `response_model` tells FastAPI (and the docs) the shape we return.

@router.post("/speak_with_kirk", response_model=ChatResponse)
def chat_with_kirk(req: ChatRequest):
    return speak_to_kirk(req)

@router.post("/speak_with_spock", response_model=ChatResponse)
def chat_with_spock(req: ChatRequest):
    return speak_to_spock(req)

@router.post("/speak_with_ship", response_model=ChatResponse)
def chat_with_ship(req: ChatRequest):
    return speak_to_ship(req)
