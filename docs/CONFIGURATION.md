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
| `GEMINI_API_KEY` | No* | API key for Gemini LLM matcher (get from [aistudio.google.com](https://aistudio.google.com/apikey)) |
| `GUIA_LABORAL_PATH` | No | Path to `guia-laboral` repo (default: `../guia-laboral`) |
| `OLLAMA_BASE_URL` | No | Ollama endpoint (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | No | Ollama model name for matching (optional alternative to Gemini) |

*\*Required only if using LLM matcher (`--llm` flag)*

## LLM Configuration

### Option A: Gemini API (recommended)

1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy the key
4. Add to `.env`:

```
GEMINI_API_KEY=AIzaSy...
```

Free tier: 60 requests per minute, more than enough for this use case.

### Option B: Ollama (local, fully offline)

Install Ollama from https://ollama.com and pull a lightweight model:

```bash
# Recommended: small, fast, good for matching
ollama pull gemma3:2b

# Alternative: more capable but slower
ollama pull llama3.2:3b
```

Then configure `.env`:

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:2b
```

Use `--llm ollama` flag to use Ollama instead of Gemini.

### Option C: No LLM (keyword matching only)

Just don't use the `--llm` flag. The keyword matcher (TF-IDF + cosine similarity) runs by default.

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
# Basic run (keyword matching only)
python -m job_harbor run

# Run with Gemini LLM matcher
python -m job_harbor run --llm

# Run with local Ollama
python -m job_harbor run --llm ollama

# Show all stored jobs
python -m job_harbor list

# Show match history
python -m job_harbor history
```

## GitHub Actions Setup

The workflow runs automatically Mon-Fri at 9 AM Chile time.

To enable the LLM matcher in CI:

1. Go to your repo → Settings → Secrets and variables → Actions
2. Add `GEMINI_API_KEY` as a repository secret
3. The workflow will use it automatically

The database persists between runs using GitHub Actions cache. You can also manually trigger a run from the Actions tab.

## Streamlit UI (v1.1, optional)

```bash
streamlit run app.py
```

Deploy to Streamlit Community Cloud:
1. Push repo to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repo and deploy
4. Add `GEMINI_API_KEY` as a Streamlit secret
