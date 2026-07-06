# 🦀 Job Harbor

> Encuentra las mejores ofertas de empleo tech alineadas a tu perfil profesional. Sin costo.

Job Harbor lee tu perfil desde [`guia-laboral`](https://github.com/MatiAlevMe/guia-laboral), busca ofertas en múltiples fuentes (LinkedIn, GetOnBoard, RemoteOK, Himalayas, Remotive, VacantesDigitales, Jooble), las matchea usando keyword matching + LLM (Gemini API free tier), y te entrega un ranking de mejores oportunidades.

**Costo total: $0**

## Stack

`Python` · `Requests` + `BeautifulSoup` · `SQLite` · `Gemini API` · `GitHub Actions`

## Arquitectura

```
┌─────────────────────────┐         ┌──────────────────────────┐
│  job-harbor (PÚBLICO)   │         │  guia-laboral (perfil)   │
│  ├─ scrapers/           │ ◄────── │  └─ resume-es.adoc        │
│  ├─ matcher/            │  lee    │                          │
│  └─ main.py             │         └──────────────────────────┘
└─────────────────────────┘
           │
           │  (ejecutado por)
           ▼
┌─────────────────────────┐
│  job-harbor-scraper     │  ← REPO PRIVADO
│  (P R I V A D O)        │     Solo este repo corre el daily
│  └─ .github/workflows/  │     scrape y guarda los resultados
│     scrape.yml          │     (no visible públicamente)
└─────────────────────────┘
```

El **código** vive en el repo público (para portfolio). El **daily scrape** y sus resultados corren en un repo privado separado, para que nadie más pueda ver ni disparar las búsquedas diarias.

## Inicio rápido (local)

```bash
git clone https://github.com/MatiAlevMe/job-harbor.git
cd job-harbor
python -m venv .venv && .venv\Scripts\activate   # o source .venv/bin/activate
pip install -e .
cp .env.example .env                              # configura GEMINI_API_KEY y JOOBLE_API_KEY
python -m job_harbor run
```

## Configurar el daily scrape (privado)

1. Crea un repo **privado** (ej: `MatiAlevMe/job-harbor-scraper`).
2. Copia `.github/workflows/scrape.private-template.yml` a ese repo como `.github/workflows/scrape.yml`.
3. En el repo privado: `Settings → Secrets and variables → Actions` y agrega:
   - `GEMINI_API_KEY` — de https://aistudio.google.com/apikey
   - `JOOBLE_API_KEY` — de https://jooble.org/api/about
   - `GH_PAT` — Personal Access Token con scope `public_repo` (para clonar `guia-laboral`)
4. Listo: corre automáticamente Lun–Vie 9:00 AM (Chile). También puedes dispararlo manualmente con `workflow_dispatch`.

> 💡 El cron y la configuración ya vienen listos en el template. Solo necesitas el repo privado + los 3 secrets.

## Fuentes de ofertas

| Scraper | Alcance |
|---------|---------|
| `linkedin` | Chile + Remote (tech) |
| `getonboard` | LATAM (feed RSS) |
| `vacantesdigitales` | LATAM (API JSON) |
| `remoteok` / `remotive` / `himalayas` | Global remoto |
| `jooble` | Multi-país (API) |

## Documentación

- [Plan del MVP](/docs/PLAN.md)
- [Guía de configuración](/docs/CONFIGURATION.md)

## Licencia

MIT
