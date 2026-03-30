# AI Presentation Coach

A PowerPoint-integrated AI coaching tool for personal use. Rehearse your presentation, get structured feedback on your slides, speech, and delivery — all inside a PowerPoint task pane.

## How it works

1. **Sync** your open deck — the add-in reads all slide text and speaker notes via Office.js
2. **Record** your rehearsal in-browser, or upload an existing audio file
3. **Analyze** — the backend transcribes your speech with Whisper, then uses an LLM to score your slides, speech quality, and how well your words matched your slides
4. **Review** feedback in the task pane — overall score, per-slide issues, and "jump to slide" navigation

```
PowerPoint Task Pane (TypeScript/React/Office.js)
        ↕  HTTP
Python Backend (FastAPI)
  ├── faster-whisper   — local audio transcription
  ├── LiteLLM          — routes to Claude / GPT / Deepseek / Ollama
  └── SQLite           — stores sessions and feedback
```

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Node.js | LTS (18+) | [nodejs.org](https://nodejs.org) |
| Python | 3.11+ | [python.org](https://python.org) or `brew install python@3.11` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| ffmpeg | any | `brew install ffmpeg` |

> **Why uv?** It replaces `pip` + `venv` with a single fast tool. `uv sync` installs all deps and creates the virtualenv in one step. `uv run` executes any command inside the managed environment without needing to activate it first.

---

## Quick start

### 1. Start the backend

```bash
./start-backend.sh
```

This runs `uv sync` (creates `.venv` and installs all dependencies) then starts the server at `http://localhost:8000`.

Add your API key to `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...
```

Verify it's running: http://localhost:8000/api/health

### 2. Start the add-in dev server

```bash
./start-addin.sh
```

This installs npm deps, generates HTTPS dev certificates, sideloads the manifest to PowerPoint, and starts webpack on `https://localhost:3000`.

### 3. Open PowerPoint

- Open any `.pptx` file
- Go to **Insert → My Add-ins** → select **Presentation Coach**
- The task pane opens on the right

---

## Changing the AI model

Edit `backend/config.yaml` — one line per task:

```yaml
llm:
  models:
    slide_analysis: "anthropic/claude-sonnet-4-20250514"
    speech_analysis: "openai/gpt-4o-mini"        # cheaper
    alignment_analysis: "deepseek/deepseek-chat"  # cost-effective
  fallback_model: "ollama/llama3"                 # local fallback
```

Any [LiteLLM-supported model](https://docs.litellm.ai/docs/providers) works — Claude, GPT, Deepseek, Qwen, Gemini, or a local Ollama model.

---

## Project structure

```
.
├── start-backend.sh          # one-command backend startup
├── start-addin.sh            # one-command add-in startup
│
├── backend/
│   ├── config.yaml           # model routing + whisper config
│   ├── .env.example          # copy to .env, add API keys
│   ├── pyproject.toml        # dependencies + uv config
│   ├── requirements.txt      # pip fallback (kept for reference)
│   └── app/
│       ├── main.py           # FastAPI app entry point
│       ├── core/
│       │   ├── config.py     # settings from config.yaml + .env
│       │   ├── database.py   # async SQLite setup
│       │   └── prompts.py    # all LLM prompt templates
│       ├── api/
│       │   ├── rehearsals.py # CRUD: create/list/get/delete sessions
│       │   ├── media.py      # audio file upload
│       │   └── analysis.py   # trigger analysis, poll status, export
│       ├── models/
│       │   └── rehearsal.py  # SQLAlchemy ORM models
│       ├── schemas/
│       │   ├── rehearsal.py  # Pydantic request/response schemas
│       │   └── feedback.py   # structured feedback schemas
│       └── services/
│           ├── transcription.py      # faster-whisper integration
│           ├── speech_analyzer.py    # WPM, filler words, LLM scoring
│           ├── slide_analyzer.py     # per-slide LLM analysis
│           ├── alignment_analyzer.py # speech vs slide coverage
│           ├── llm_client.py         # LiteLLM wrapper + fallback
│           └── export.py             # markdown feedback export
│
└── powerpoint-addin/
    ├── manifest.xml          # Office Add-in manifest
    ├── package.json
    ├── webpack.config.js     # HTTPS dev server on :3000
    └── src/taskpane/
        ├── index.tsx         # Office.onReady bootstrap
        ├── types/index.ts    # shared TypeScript interfaces
        ├── hooks/
        │   └── usePolling.ts # polls analysis status until complete
        ├── services/
        │   ├── apiClient.ts      # typed HTTP client for all endpoints
        │   ├── slideExtractor.ts # Office.js slide text extraction
        │   ├── slideNavigator.ts # "jump to slide" via PowerPoint API
        │   └── audioRecorder.ts  # MediaRecorder wrapper (pause/resume)
        └── components/
            ├── App.tsx               # 4-tab shell
            ├── DeckSync.tsx          # sync slides, create session
            ├── RecordingPanel.tsx    # record/upload + start analysis
            ├── AnalysisProgress.tsx  # step-by-step progress display
            ├── FeedbackDashboard.tsx # overall score + tabbed feedback
            ├── SlideCard.tsx         # per-slide score + go-to-slide
            └── SessionHistory.tsx    # past sessions list
```

---

## Development

All backend commands use `uv run` — no manual venv activation needed.

```bash
cd backend

# Install all deps (runtime + dev) into .venv
uv sync

# Run the server
uv run uvicorn app.main:app --reload

# Run all tests
uv run pytest

# Run only unit tests
uv run pytest tests/unit/

# Run only functional tests
uv run pytest tests/functional/

# Run a single test by name
uv run pytest -k "test_wpm"

# Add a new runtime dependency
uv add some-package

# Add a dev-only dependency
uv add --dev some-package
```

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/rehearsals` | Create session with slide data |
| `GET` | `/api/rehearsals` | List all sessions |
| `GET` | `/api/rehearsals/{id}` | Get session detail |
| `DELETE` | `/api/rehearsals/{id}` | Delete session |
| `POST` | `/api/rehearsals/{id}/audio` | Upload audio file |
| `POST` | `/api/rehearsals/{id}/analyze` | Start analysis (async) |
| `GET` | `/api/rehearsals/{id}/results` | Poll results + status |
| `GET` | `/api/rehearsals/{id}/export` | Download markdown feedback |

Interactive docs: http://localhost:8000/docs

---

## Analysis pipeline

```
Upload audio
     ↓
faster-whisper (local, CPU) → transcript + timestamps
     ↓
┌─────────────────────────────────┐
│  Slide analysis   (per slide)   │  LLM scores clarity, density, structure
│  Speech analysis  (transcript)  │  LLM scores pace, filler words, clarity
│  Alignment check  (both)        │  LLM checks coverage + coherence
└─────────────────────────────────┘
     ↓
Overall summary LLM call → headline + top 3 strengths/improvements
     ↓
Results stored in SQLite, surfaced in task pane
```

Analysis runs as a FastAPI background task. The task pane polls `/results` every 3 seconds until status is `complete` or `failed`.

---

## In-browser recording

The add-in uses `MediaRecorder` for in-browser recording. This works in most desktop WebViews, but Office on Mac may restrict microphone access. If recording is blocked, use the file upload option (accepts `.webm`, `.mp3`, `.wav`, `.ogg`, `.m4a`).

---

## Notes on speaker notes extraction

Speaker notes require PowerPoint JavaScript API 1.3+. The add-in checks `isSetSupported('PowerPointApi', '1.3')` at runtime and degrades gracefully — notes will be empty if the API version is too low, but slide text analysis still works.

---

## Limitations (v1)

- Local-only, no auth
- No real-time live coaching
- No video / nonverbal analysis
- Mac PowerPoint WebView may block in-browser recording (use file upload)
- Whisper `base` model trades speed for accuracy — upgrade to `small` or `medium` in `config.yaml` for better results on accented speech
