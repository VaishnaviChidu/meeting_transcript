# Workspace instructions

- Keep the MVP transcript-only. Do not add audio processing or external integrations without confirmation.
- Backend: FastAPI, Pydantic, LangGraph, SQLite, Chroma, and Google Gemini. Frontend: React, TypeScript, Vite.
- Keep API keys in environment variables; never commit `.env` or generated meeting data.
- Assign owners only from explicit transcript speaker labels; clear unmatched names and route them to clarification. Do not guess deadlines. Preserve evidence for every extracted item.
- Validate backend changes with `pytest` and frontend changes with `npm run build`.

## Setup progress

- [x] Clarified project type, stack, input, provider, and interface with the user.
- [x] Scaffolded backend and frontend.
- [x] Implemented transcript analysis, context indexing, result persistence, and clarification resume flow.
- [x] Added tests and local setup instructions.
- [x] Required extensions: none.
- [x] Backend dependencies installed in the configured Python environment; `pytest` passes (4 tests).
- [x] Frontend dependencies installed and `npm run build` passes.
- [ ] Ask before launching long-running services.
