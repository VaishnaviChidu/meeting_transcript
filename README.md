# Meetwise

A local-first meeting-notes MVP. Paste or upload a text transcript, retrieve relevant team/project context, draft a summary and decisions, identify action items with transcript evidence, and pause the LangGraph workflow for human clarification when ownership or wording is ambiguous.

## Requirements

- Python 3.11+
- Node.js 20+
- A Google AI Studio API key for live analysis, embeddings, and context indexing (Gemini's free tier has usage limits)

The web UI and API can start without a key, but analysis/context routes will return a setup message until `GOOGLE_API_KEY` is configured. The Gemini API free tier has quotas and Google may use submitted content to improve its products; do not send confidential transcripts unless that is acceptable. Transcripts and workflow state are stored locally under `data/` (ignored by Git). This prototype has no authentication, authorization, or production-grade retention controls. Do not expose it publicly.

## Run locally

1. Create a virtual environment and install backend dependencies:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`, then add a Google AI Studio API key. `.env` is git-ignored. The default model is `gemini-3.8-flash`; free-tier access and quotas are subject to Google's current policies.
3. Start the API from the repository root:

   ```sh
   uvicorn backend.app.main:app --reload --port 8000
   ```

4. In another terminal, install and start the web client:

   ```sh
   npm install
   npm run dev
   ```

5. Open the Vite URL shown in the terminal (typically `http://localhost:5173`). Paste a transcript or upload a `.txt` file. Use the team/project context panel to index names, roles, glossary terms, and project briefs before analyzing a meeting.

After switching from the former OpenAI setup, re-index any team/project context documents; Gemini embeddings use a separate local Chroma collection.

## API overview

- `GET /api/health` — API status and whether the LLM key is configured.
- `POST /api/context` — embed and index a named context document.
- `POST /api/meetings` — analyze a meeting transcript; returns a draft and any clarification prompts.
- `POST /api/meetings/{id}/clarifications` — resume the persisted workflow with answers.
- `GET /api/meetings/{id}` — retrieve the stored result.

The extraction uses structured output and attaches transcript evidence to decisions and actions. An action owner must match a labeled speaker who explicitly accepts or is clearly assigned the work; unmatched owners are cleared and sent for clarification. Missing owners and marked ambiguities trigger clarification; the application deliberately does not guess. Retrieved context helps resolve team/project references, but the transcript remains the evidence source for meeting claims.

## Checks

- Frontend type-check and production build: `npm run build`
- Backend tests: `pytest`

## MVP boundaries

Input is transcript text only; audio transcription, identity/login, meeting-platform integrations, outbound task creation, and production deployment are not included. SQLite and Chroma are local development storage choices. Review AI-generated drafts before sharing them.
# meeting_transcript
