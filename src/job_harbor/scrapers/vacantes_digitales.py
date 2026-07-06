"""VacantesDigitales scraper — uses the public JSON API (no auth required)."""

import re
from typing import Optional

import requests

from .base import Scraper
from ..model import Job


API_URL = "https://vacantesdigitales.com/api/vacancies"

TECH_CATEGORIES = {"desarrollo", "data", "devops", "qa", "mobile", "seguridad", "ux-ui", "producto"}
NON_TECH_CATEGORIES = {"ventas", "marketing", "finanzas", "rrhh", "administracion", "legal"}


class VacantesDigitalesScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        jobs: list[Job] = []
        page = 1

        try:
            while len(jobs) < limit:
                resp = requests.get(
                    API_URL,
                    params={"page": page, "limit": 20},
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/131.0.0.0 Safari/537.36"
                        ),
                    },
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data.get("data", [])
                if not raw:
                    break

                for entry in raw:
                    if len(jobs) >= limit:
                        break
                    job = self._parse_job(entry)
                    if job:
                        jobs.append(job)

                page += 1
                pagination = data.get("pagination", {})
                total_pages = pagination.get("total_pages", 1) if isinstance(pagination, dict) else 1
                if page > total_pages:
                    break

        except Exception:
            pass

        return jobs

    def _parse_job(self, entry: dict) -> Optional[Job]:
        title = (entry.get("title") or "").strip()
        company_data = entry.get("company") or {}
        company = ""
        if isinstance(company_data, dict):
            company = (company_data.get("name") or "").strip()
        elif isinstance(company_data, str):
            company = company_data.strip()
        url = (entry.get("post_url") or "").strip()
        description = (entry.get("copy_seo_raw") or entry.get("copy_seo") or "").strip()
        skills_raw = entry.get("skills") or []
        category = (entry.get("job_category") or "").strip().lower()
        location_type = entry.get("job_location_type") or ""
        experience = (entry.get("experience") or "").strip()
        employment = (entry.get("employment_type") or "").strip()
        salary = entry.get("salary")
        position = (entry.get("position") or "").strip()

        if not title or not url:
            return None

        if category in NON_TECH_CATEGORIES:
            return None

        if category not in TECH_CATEGORIES:
            title_lower = (title + " " + position).lower()
            tech_words = [
                "engineer", "developer", "programmer", "software",
                "full stack", "backend", "frontend", "devops",
                "data", "qa", "test", "automation", "python",
                "java", "javascript", "ruby", "rails",
                "react", "node", "cloud", "ml", "ai",
            ]
            if not any(w in title_lower for w in tech_words):
                return None

        remote = "telecommute" in location_type.lower() or "remoto" in title.lower()
        skills_str = ", ".join(skills_raw) if isinstance(skills_raw, list) else ""
        combined_desc = f"{title} {company} {category} {skills_str} {description}".strip()

        salary_str = str(salary) if salary else ""

        return Job(
            title=title,
            company=company or "Sin especificar",
            location="LATAM - Remoto" if remote else "LATAM",
            remote=remote,
            url=url,
            description=combined_desc[:3000],
            requirements=skills_str,
            source="vacantesdigitales",
            salary_range=salary_str,
        )
