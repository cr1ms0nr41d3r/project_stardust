# Project Stardust — Aboard The Crusader

A three-stage browser game served by a small FastAPI app. Stage 2 talks to Gemini over a WebSocket so you can ask Kirk, Spock, and the ship’s Computer about real exoplanets.

```
Browser (static/)  --HTTP / WS-->  FastAPI (main.py)
                                      |-- tools/gemini.py  --> Gemini
                                      |-- tools/nasa.py    --> NASA Exoplanet Archive / APOD
```

## Setup

```bash
uv sync
cp .env.example .env   # then put your Gemini key in .env
```

Get a free Gemini key at https://aistudio.google.com/apikey. `NASA_API_KEY` is optional (APOD falls back to NASA’s `DEMO_KEY`).

## Run

```bash
uv run uvicorn main:app --reload
```

Open http://127.0.0.1:8000/ to play. API docs: http://127.0.0.1:8000/docs

Stages 1 and 3 work with no API key. Stage 2 crew chat needs `GEMINI_API_KEY`.

## Useful endpoints

- `GET /` — game
- `GET /health` — liveness
- `GET /planets` — six survey worlds (live NASA data, cached, then bundled fallback)
- `WS /ws` — Stage 2 crew chat (`{character, message, planet}`)
- `POST /speak_with_captain` / `_scribe` / `_ship` — plain-text chat for `/docs` testing
