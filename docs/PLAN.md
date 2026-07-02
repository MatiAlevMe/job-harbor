# Job Harbor — Plan del MVP

## Objetivo

Aplicación que lee el perfil profesional desde `guia-laboral`, busca ofertas de empleo en múltiples fuentes, las matchea contra el perfil usando keyword matching + LLM (Gemini API free tier o Ollama local), y entrega un ranking de mejores oportunidades.

## Stack

| Componente | Tecnología | Costo |
|------------|-----------|-------|
| Lenguaje | Python 3.12+ | $0 |
| Scraping | Playwright + BeautifulSoup | $0 |
| Base de datos | SQLite | $0 |
| Keyword matcher | TF-IDF + cosine similarity (scikit-learn) | $0 |
| LLM matcher | Gemini API free tier o Ollama local | $0 |
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
│  1. Profile Loader         │ ← Lee ADOC desde el repo guia-laboral
│     src/job_harbor/profile │    (sibling directory o GUIA_LABORAL_PATH)
└───────────┬────────────────┘
            ▼
┌────────────────────────────┐      ┌─────────────────┐
│  2. Scrapers               │ ──→  │  SQLite (jobs)  │
│     src/job_harbor/scrapers │      │  jobs.db        │
│  · Google Jobs (Playwright) │      └────────┬────────┘
│  · GetOnBoard (Playwright)  │               │
│  · RemoteOK (Playwright)   │               ▼
└───────────┬────────────────┘      ┌────────────────────────────┐
            ▼                       │  3. Matcher                │
┌────────────────────────────┐      │  src/job_harbor/matcher    │
│  4. Output CLI             │ ◄─── │  · Keyword (TF-IDF)        │
│     src/job_harbor/main.py │      │  · LLM (Gemini/Ollama)     │
└────────────────────────────┘      └────────────────────────────┘
            ▼
┌────────────────────────────┐
│  5. GitHub Actions cron    │ ← Corre L-V, cachea jobs.db
│  .github/workflows/        │    Sube artifact + summary
└────────────────────────────┘
            ▼
┌────────────────────────────┐
│  6. Streamlit (v1.1)       │ ← Dashboard web (scaffolded)
│  app.py                    │
└────────────────────────────┘
```

## ¿Cómo lee el CV?

**Localmente:**
- Busca `../guia-laboral/cv/cv-es.adoc` (relativo al repo `job-harbor`)
- Si `guia-laboral` está en `E:\repos\guia-laboral`, el path `../guia-laboral` resuelve correctamente desde `E:\repos\job-harbor`
- Se puede sobreescribir con `GUIA_LABORAL_PATH` en `.env`
- Si no encuentra nada, usa un perfil default con skills hardcodeados

**En GitHub Actions:**
- Hace checkout del repo `MatiAlevMe/guia-laboral` como sibling
- El repo debe ser **público** (no necesita token) o tener un `GH_PAT` configurado

## Fuentes de datos

| Fuente | Método | Prioridad | Cobertura |
|--------|--------|-----------|-----------|
| Google Jobs | Playwright | 1 | LinkedIn, Indeed, portales chilenos, etc. |
| GetOnBoard | Playwright | 2 | Portal tech chileno, ofertas remotas |
| RemoteOK | Playwright | 3 | Internacional, remoto, acepta LATAM |
| AngelList / WeWorkRemotely | HTTP + BS4 | 4 (post-MVP) | Startups, remoto global |

## Matcher

### Nivel 1 — Keyword (siempre corre)
- Vectoriza perfil + descripción con TF-IDF
- Calcula cosine similarity
- Skills match: intersección de skills del perfil vs requisitos
- Location match: filtro por ubicaciones preferidas
- Score normalizado 0-100

### Nivel 2 — LLM (opcional, flag `--llm`)
- Backends: Gemini API (`gemini`) o Ollama local (`ollama`)
- Envía top N ofertas al modelo para evaluación semántica
- Output: puntaje ajustado + explicación en lenguaje natural
- Gemini free tier: 10-15 RPM, 1,500 RPD (modelos: 2.5 Flash, 3 Flash, 3.1 Flash-Lite)
- Ollama: offline, sin límites, con `phi4-mini` recomendado

## Output (CLI)

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

## Output (GitHub Actions)

- **Cache:** `jobs.db` persistido entre runs (no duplica ofertas)
- **Artifact:** `job-results` descargable por 30 días
- **Summary:** Tabla markdown con top 10 matches visible en la UI de Actions
- **Logs:** Total de ofertas encontradas vs matcheadas
- **Notificaciones:** ❌ No implementado (v2)

## Lo que NO incluye el MVP

- LinkedIn scraping directo (Google Jobs lo cubre parcialmente)
- Alertas por WhatsApp/Telegram/OpenClaw (v2)
- Scraping de sitios directos de empresas (Kibernum, Globant, etc.) (v3)
- Matching semántico avanzado con fine-tuning

## Roadmap

| Versión | Alcance |
|---------|---------|
| v1.0 MVP | Profile loader + 3 scrapers + SQLite + Keyword matcher + CLI + GitHub Actions |
| v1.1 | Streamlit UI + LLM matcher configurable por .env |
| v2.0 | OpenClaw skill + alertas por Telegram/WhatsApp |
| v2.1 | Notificaciones push vía GitHub Notifications / email |
| v3.0 | Más fuentes (empresas directas, portales internacionales) |
| v3.1 | Mejora de selectores de scraping (mantenimiento continuo) |
