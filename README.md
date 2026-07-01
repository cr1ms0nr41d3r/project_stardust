# Gemini Chatbot — a tiny teaching server

A minimal FastAPI server with one chat endpoint that talks to Google's Gemini
model. The whole thing is in [main.py](main.py) and is commented like a lesson.

## The big picture

```
   You (browser/curl)  --HTTP-->  FastAPI server  --API call-->  Gemini (Google)
            ^                          (main.py)                       |
            |__________________________ reply ___________________________|
```

- **FastAPI** is the web server: it waits for requests and returns responses.
- **Gemini** is the LLM (Large Language Model): give it text, it returns text.
- **Chatbot** = the glue: take the user's message, ask Gemini, return its reply.

## Setup

1. Install dependencies (this project uses [uv](https://docs.astral.sh/uv/)):

   ```bash
   uv sync
   ```

2. Get a free API key at https://aistudio.google.com/apikey and set it:

   ```powershell
   # PowerShell
   $env:GEMINI_API_KEY = "your-key-here"
   ```

   ```bash
   # bash / zsh
   export GEMINI_API_KEY="your-key-here"
   ```

3. Or if you want you can set your api key directly in the .env file:
   ```md
   # Copy this file to ".env" and put your real key in it.
   #   PowerShell:  Copy-Item .env.example .env
   #   bash/zsh:    cp .env.example .env
   #
   # Get a free key at: https://aistudio.google.com/apikey
   # The .env file is gitignored, so your key never gets committed.

   GEMINI_API_KEY=your-key-here
   ```

## Run it

```bash
uv run uvicorn main:app --reload
```

The server starts at http://127.0.0.1:8000. The `--reload` flag restarts it
automatically whenever you edit the code — handy while learning.

## Try it

Open the auto-generated, interactive API docs in your browser:

> http://127.0.0.1:8000/docs

FastAPI builds this page for free from the code. Click **POST /chat**, then
**Try it out**, and send a message.

Or from the command line:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Explain what an API is in one sentence.\"}"
```

Response:

```json
{ "reply": "An API is a contract that lets two programs talk to each other..." }
```

## Where to go next

- Give the bot a personality with a system instruction.
- Remember previous messages so it can hold a conversation (chat history).
- Stream the reply word-by-word instead of waiting for the whole answer.
