# PJASensei Socratic Tutor Prototype

AI-powered tutoring prototype that gives students progressively stronger hints before revealing a full solution.

## Run locally

Requires Node.js 20+ and Python 3.9+.

```bash
npm install
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm run dev
```

Open `http://localhost:5173/`.

The Python API runs on `http://localhost:8787/` and the Vite dev server proxies `/api` requests to it.

## LLM configuration

Copy `.env.example` to `.env` and set:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_BASE_URL=https://api.openai.com/v1
```

Any OpenAI-compatible `/chat/completions` endpoint can be used by changing `OPENAI_API_BASE_URL`. If no API key is present, the server uses deterministic fallback hints so the prototype still works offline.

## Architecture

- `src/App.tsx` contains the React tutoring workspace and session persistence.
- `server/main.py` exposes the FastAPI tutor API.
- `server/hint_manager.py` owns hint levels, session state, solution reveal rules, and next-action decisions.
- `server/openai_client.py` isolates the OpenAI-compatible API call and fallback generation.
- `server/models.py` defines the backend request, response, session, and message models.
- `shared/types.ts` defines the matching client-side TypeScript types used by the React app.

Hint progression:

1. Subtle guidance
2. Relevant concepts
3. Specific method or strategy
4. Next concrete step
5. Almost complete solution outline
6. Full solution

The full solution is only returned when the student clicks **Show Solution** or asks for another hint after reaching level 5.
