"""LLM-based matcher using Gemini API (free tier) or local Ollama.

Evaluates jobs semantically against the user's profile and provides
natural language reasoning for each match score.
"""

import os
import json
import re
import time
from typing import Optional

from ..model import Profile, Job

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


class LLMMatcher:
    def __init__(self, profile: Profile, backend: str = "gemini"):
        self.profile = profile
        self.backend = backend

    def _build_prompt(self, job: Job) -> str:
        raw = self.profile.raw_text
        raw = raw[:3000] if raw else ""
        return f"""Eres un reclutador experto evaluando qué tan bien calza una oferta con un perfil.

## Perfil estructurado del candidato
- Rol: {self.profile.title}
- Skills: {', '.join(self.profile.skills)}
- Años de experiencia: {self.profile.experience_years}
- Educación: {self.profile.education}
- Ubicaciones preferidas: {', '.join(self.profile.locations)}
- Roles preferidos: {', '.join(self.profile.preferred_roles)}

## Experiencia completa del candidato (Resume)
{raw}

## Oferta
- Título: {job.title}
- Empresa: {job.company}
- Ubicación: {job.location}
- Remoto: {job.remote}
- Descripción: {job.description[:2000]}

## Instrucciones
- El candidato tiene {self.profile.experience_years} años de experiencia profesional. Penaliza fuertemente ofertas que requieran mucha más experiencia (Senior, Staff, Principal, Lead, 5+ años requeridos).
- Penaliza ofertas cuya ubicación geográfica no sea accesible desde Chile (ej: requiere estar en USA, Europa, UK, o tener permiso de trabajo en otro país).
- El candidato busca trabajo remoto mundial o presencial en Chile. Valora positivamente ofertas remotas sin restricción geográfica.

Devuelve SOLO un JSON válido en este formato (sin markdown, sin explicación adicional):
{{
  "score": <0-100>,
  "skills_match": ["skill1", "skill2"],
  "skills_gap": ["skill3", "skill4"],
  "reason": "explicación breve en español de por qué calza o no"
}}"""

    def match(self, job: Job) -> tuple[float, str, list[str], list[str]]:
        if self.backend == "ollama":
            return self._match_ollama(job)
        return self._match_gemini(job)

    def _match_gemini(self, job: Job) -> tuple[float, str, list[str], list[str]]:
        if not HAS_GEMINI:
            return self._fallback(job)

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return self._fallback(job)

        for attempt in range(3):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=self._build_prompt(job),
                )
                text = response.text.strip()
                text = text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)

                score = min(100, max(0, data.get("score", 0)))
                skills_match = data.get("skills_match", [])
                skills_gap = data.get("skills_gap", [])
                reason = data.get("reason", "Evaluado por Gemini")

                return score, reason, skills_match, skills_gap

            except Exception as e:
                estr = str(e)
                is_quota = "429" in estr or "RESOURCE_EXHAUSTED" in estr or "quota" in estr.lower()
                is_server_error = "500" in estr or "503" in estr or "INTERNAL" in estr or "unavailable" in estr.lower()
                if (is_quota or is_server_error) and attempt < 2:
                    m = re.search(r"retry in ([\d.]+)s", estr)
                    delay = float(m.group(1)) + 2 if m else (60 if is_server_error else 45)
                    tag = "server error" if is_server_error else "quota"
                    print(f"  [dim]Gemini {tag}, retrying in {delay:.0f}s...[/dim]")
                    time.sleep(delay)
                    continue
                print(f"  [dim]Gemini error: {e}[/dim]")
                return self._fallback(job)

        return self._fallback(job)

    def _match_ollama(self, job: Job) -> tuple[float, str, list[str], list[str]]:
        try:
            import requests
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.environ.get("OLLAMA_MODEL", "phi4-mini")
            response = requests.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": self._build_prompt(job), "stream": False},
                timeout=30,
            )
            text = response.json().get("response", "")
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)

            score = min(100, max(0, data.get("score", 0)))
            skills_match = data.get("skills_match", [])
            skills_gap = data.get("skills_gap", [])
            reason = data.get("reason", "Evaluado por Ollama")

            return score, reason, skills_match, skills_gap

        except Exception:
            return self._fallback(job)

    def _fallback(self, job: Job) -> tuple[float, str, list[str], list[str]]:
        return (0.0, "LLM no disponible", [], [])
