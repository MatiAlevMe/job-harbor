# 🦀 Job Harbor

> Encuentra las mejores ofertas de empleo tech alineadas a tu perfil profesional. Sin costo.

Job Harbor lee tu perfil desde `guia-laboral`, busca ofertas en múltiples fuentes (Google Jobs, GetOnBoard, RemoteOK), las matchea usando keyword matching + LLM (Gemini API free tier), y te entrega un ranking de mejores oportunidades.

Automático con GitHub Actions — corre gratis cada día hábil.

## Stack

`Python` · `Playwright` · `SQLite` · `scikit-learn` · `Gemini API` · `GitHub Actions` · `Streamlit`

**Costo total: $0**

## Inicio rápido

```bash
git clone https://github.com/MatiAlevMe/job-harbor.git
cd job-harbor
python -m venv .venv && .venv\Scripts\activate  # o source .venv/bin/activate
pip install -e .
playwright install chromium
cp .env.example .env  # Configura tu GEMINI_API_KEY
python -m job_harbor run
```

## Documentación

- [Plan del MVP](/docs/PLAN.md)
- [Guía de configuración](/docs/CONFIGURATION.md)

## Licencia

MIT
