# Job Harbor — Plan del MVP

## Objetivo

Aplicación que lee el perfil profesional desde `guia-laboral`, busca ofertas de empleo en múltiples fuentes, las matchea contra el perfil usando keyword matching + LLM (Gemini API free tier), y entrega un ranking de mejores oportunidades.

## Stack

| Componente | Tecnología | Costo |
|------------|-----------|-------|
| Lenguaje | Python 3.12+ | $0 |
| Scraping | Playwright + BeautifulSoup | $0 |
| Base de datos | SQLite | $0 |
| Keyword matcher | TF-IDF + cosine similarity (scikit-learn) | $0 |
| LLM matcher | Gemini API free tier | $0 |
| Automatización | GitHub Actions (cron) | $0 |
| Interfaz web (opcional) | Streamlit Community Cloud | $0 |

**Costo total del proyecto: $0**

## Arquitectura

```
guia-laboral/ (repo externo, ruta relativa)
  └── cv/cv-es.adoc
  └── resume/resume-es.adoc
       │
       ▼
┌────────────────────────────┐
│  1. Profile Loader         │ ← Lee ADOC, extrae perfil
│     src/job_harbor/profile │
└───────────┬────────────────┘
            ▼
┌────────────────────────────┐      ┌─────────────────┐
│  2. Scrapers               │ ──→  │  SQLite (jobs)  │
│     src/job_harbor/scrapers │      │  jobs.db        │
│  · Google Jobs (Playwright) │      └────────┬────────┘
│  · GetOnBoard (Playwright)  │               │
│  · RemoteOK (HTTP+BS4)     │               ▼
└───────────┬────────────────┘      ┌────────────────────────────┐
            ▼                       │  3. Matcher                │
┌────────────────────────────┐      │  src/job_harbor/matcher    │
│  4. Output CLI             │ ◄─── │  · Keyword (TF-IDF)        │
│     src/job_harbor/main.py │      │  · LLM (Gemini) opcional   │
└────────────────────────────┘      └────────────────────────────┘
            ▼
┌────────────────────────────┐
│  5. GitHub Actions cron    │
│  .github/workflows/        │
└────────────────────────────┘
            ▼
┌────────────────────────────┐
│  6. Streamlit (v1.1)       │
│  app.py                    │
└────────────────────────────┘
```

## Fuentes de datos

| Fuente | Método | Prioridad | Cobertura |
|--------|--------|-----------|-----------|
| Google Jobs | Playwright | 1 | LinkedIn, Indeed, portales chilenos, etc. |
| GetOnBoard | Playwright | 2 | Portal tech chileno, ofertas remotas |
| RemoteOK | HTTP + BS4 | 3 | Internacional, remoto, acepta LATAM |
| AngelList / WeWorkRemotely | HTTP + BS4 | 4 (post-MVP) | Startups, remoto global |

## Matcher

### Nivel 1 — Keyword (siempre corre)
- Vectoriza perfil + descripción con TF-IDF
- Calcula cosine similarity
- Skills match: intersección de skills del perfil vs requisitos
- Location match: filtro por ubicaciones preferidas
- Score normalizado 0-100

### Nivel 2 — LLM (opcional, flag `--llm`)
- Envía top N ofertas a Gemini API
- Evaluación semántica: "¿Qué tan bien calza esta oferta con el perfil?"
- Output: puntaje ajustado + explicación en lenguaje natural
- Gratis: Gemini API free tier (60 req/min)

## Output esperado

```
$ python -m job_harbor run

Job Harbor — 48 ofertas analizadas | 12 relevantes

🥇 92% QA Automation Engineer — BC Tecnología
   Skills: Python, SQL, Selenium, Jenkins ✅
   Gap: Cypress, Playwright ⚠️
   → https://getonboard.cl/...

🥈 85% Backend Engineer — Xepelin
   Skills: Python, CI/CD, AWS ✅
   Gap: Node.js, TypeScript ⚠️
   → ...
```

## Lo que NO incluye el MVP

- LinkedIn scraping directo (Google Jobs lo cubre parcialmente; scraping directo es riesgoso)
- Alertas por WhatsApp/Telegram/OpenClaw (v2)
- Scraping de sitios directos de empresas (Kibernum, Globant, etc.) (v3)
- Matching semántico avanzado con fine-tuning

## Roadmap

| Versión | Alcance |
|---------|---------|
| v1.0 MVP | Profile loader + 3 scrapers + SQLite + Keyword matcher + CLI + GitHub Actions |
| v1.1 | Streamlit UI + Gemini LLM matcher |
| v2.0 | OpenClaw skill + alertas por Telegram |
| v3.0 | Más fuentes (empresas directas, portales internacionales) |
