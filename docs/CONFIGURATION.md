# Configuration Guide

## Prerequisites

- Python 3.12+
- Git
- Playwright browsers (installed automatically)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/MatiAlevMe/job-harbor.git
cd job-harbor
```

### 2. Create virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Install Playwright browsers

```bash
playwright install chromium
```

### 5. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | No* | API key for Gemini LLM matcher ([get one free](https://aistudio.google.com/apikey)) |
| `GEMINI_MODEL` | No | Gemini model name (default: `gemini-2.5-flash`) |
| `GUIA_LABORAL_PATH` | No | Path to `guia-laboral` repo (default: `../guia-laboral`) |
| `OLLAMA_BASE_URL` | No | Ollama endpoint (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | No | Ollama model name (default: `phi4-mini`) |

*\*Required only if using LLM matcher (`--llm` flag)*

## How the profile (CV) is loaded

The tool reads your CV from the `guia-laboral` repo to extract your skills, experience, and preferences.

**Local mode:** It looks for `../guia-laboral/cv/cv-es.adoc` (sibling directory). If both repos are inside `E:\repos\`, the relative path `../guia-laboral` resolves correctly. If the repo is elsewhere, set `GUIA_LABORAL_PATH` in `.env`.

**GitHub Actions:** The workflow checks out `MatiAlevMe/guia-laboral` as a sibling directory. The repo must be **public** (recommended) or you must create a `GH_PAT` secret with repo access.

**Fallback:** If no `guia-laboral` repo is found, a default profile is used with all your known skills.

## LLM Configuration

### Option A: Gemini API (online, free tier)

1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy the key
4. Add to `.env`:

```
GEMINI_API_KEY=AIzaSy...
```

**Available free models (2026):**

| Model | Status | Rate |
|-------|--------|------|
| `gemini-2.5-flash` | ✅ Free (default) | 10 RPM, 1,500 RPD |
| `gemini-3-flash` | ✅ Free | 10 RPM, 1,500 RPD |
| `gemini-3.1-flash-lite` | ✅ Free | 15 RPM, 1,000 RPD |

Set your preferred model:

```
GEMINI_MODEL=gemini-2.5-flash
```

> **Note:** `gemini-2.0-flash-lite` was deprecated and shut down on June 1, 2026. The code now uses `gemini-2.5-flash` by default.

### Option B: Ollama (local, fully offline)

Use Ollama with a model you already have installed. Recommended for your system:

```bash
# Already installed ✅
ollama run phi4-mini
```

Configure `.env`:

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi4-mini
```

Run with:

```bash
python -m job_harbor run --llm ollama
```

Other models you have installed: `qwen3:1.7b` (lighter), `qwen3:8b` (better quality), `deepseek-r1:7b`.

### Option C: No LLM (keyword matching only)

Just don't use the `--llm` flag. The keyword matcher (TF-IDF + cosine similarity) runs by default.

```bash
python -m job_harbor run
```

## Profile Configuration

The profile is automatically loaded from `guia-laboral/cv/cv-es.adoc`. If the repo is not at the default location, set `GUIA_LABORAL_PATH` in `.env`.

You can also override preferences in `config.yaml` (auto-created on first run):

```yaml
preferences:
  locations:
    - "Valparaíso"
    - "Santiago"
    - "Remoto Chile"
    - "Remoto Mundial"
  min_match_score: 50
  keywords:
    - "QA"
    - "Automation"
    - "Full Stack"
    - "Backend"
    - "Python"
    - "Rails"
```

## Running

```bash
# Basic run (keyword matching only, no LLM)
python -m job_harbor run

# Run with Gemini LLM matcher (default Gemini)
python -m job_harbor run --llm

# Run with specific backend
python -m job_harbor run --llm gemini
python -m job_harbor run --llm ollama

# Show all stored jobs
python -m job_harbor list

# Show match history
python -m job_harbor history
```

## GitHub Actions Setup

The workflow runs automatically Mon-Fri at 9 AM Chile time.

### Setup steps:

1. Make `guia-laboral` repo **public** (recommended) — no token needed for checkout.
   - Or add `GH_PAT` as a repo secret if you want to keep it private.
2. Go to your repo → Settings → Secrets and variables → Actions
3. Add `GEMINI_API_KEY` as a repository secret (optional, needed only for LLM matching)
4. Optionally add `GEMINI_MODEL` as a secret if you want a non-default model

### Where do results go?

| Output | Location | How to access |
|--------|----------|---------------|
| **Database** | GitHub Actions cache | Persists between runs automatically |
| **Artifact** | Actions → Run → Artifacts | Download `job-results` (the `jobs.db` file) |
| **Summary** | Actions → Run → Summary | Table of top 10 matches, visible in GitHub UI |
| **Notifications** | ❌ Not included (v2) | Planned: Telegram/WhatsApp via OpenClaw |

### Understanding job-match scores from GitHub Actions

The Step Summary shows your top 10 matches as a markdown table:

```
## Job Harbor Results
- [92%] BC Tecnología — QA Automation Engineer
- [85%] Xepelin — Backend Engineer
```

Each workflow run also:
- Caches the SQLite DB so duplicates aren't re-saved
- Uploads the DB as an artifact for 30 days
- Shows total offers found vs matched in the workflow logs

## Post-MVP (Future)

See `docs/PLAN.md` for the full roadmap. Planned improvements:

- **v1.1** Streamlit UI (web dashboard) — already scaffolded as `app.py`
- **v2.0** OpenClaw skill + Telegram/WhatsApp alerts
- **v3.0** More sources (Kibernum, Globant, Accenture direct scraping; AngelList, WeWorkRemotely)

## Streamlit UI (v1.1, optional)

```bash
streamlit run app.py
```

Deploy to Streamlit Community Cloud:
1. Push repo to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repo and deploy
4. Add `GEMINI_API_KEY` as a Streamlit secret
