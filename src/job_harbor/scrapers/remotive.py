"""Remotive scraper — uses the public JSON API (no auth required)."""

import re
from typing import Optional

import requests

from .base import Scraper
from ..model import Job


API_URL = "https://remotive.com/api/remote-jobs"

TECH_CATEGORIES = {
    "Software Development",
    "Quality Assurance",
    "Artificial Intelligence",
    "Data and Analytics",
    "DevOps / Sysadmin",
    "Product Management",
    "Engineering",
    "Technical Support",
}

NON_TECH_TITLE_WORDS = [
    "writer", "writing", "content", "copywriter", "editor", "proofreader",
    "sales", "marketing", "hr", "recruiter", "social media",
    "customer support", "virtual assistant", "medical", "nurse",
    "teacher", "tutor", "professor", "coach",
    "accountant", "finance", "legal", "paralegal",
    "driver", "delivery", "operator", "crew",
]


class RemotiveScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        jobs: list[Job] = []

        try:
            params = {"limit": 100}
            resp = requests.get(
                API_URL,
                params=params,
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
            raw = data.get("jobs", [])

            for entry in raw:
                if len(jobs) >= limit:
                    break
                job = self._parse_job(entry)
                if job:
                    jobs.append(job)

        except Exception:
            pass

        return jobs

    def _parse_job(self, entry: dict) -> Optional[Job]:
        title = (entry.get("title") or "").strip()
        company = (entry.get("company_name") or "").strip()
        link = (entry.get("url") or "").strip()
        description = (entry.get("description") or "")
        category = (entry.get("category") or "")
        location = (entry.get("candidate_required_location") or "Worldwide").strip()
        salary = (entry.get("salary") or "").strip()
        tags = entry.get("tags") or []

        if not title or not link:
            return None

        if category not in TECH_CATEGORIES:
            return None

        title_lower = title.lower()
        if any(w in title_lower for w in NON_TECH_TITLE_WORDS):
            return None

        remote = "worldwide" in location.lower() or "remote" in location.lower()
        tag_str = ", ".join(tags) if tags else ""
        combined_desc = f"{title} {company} {tag_str} {description}".strip()

        return Job(
            title=title,
            company=company or "Sin especificar",
            location=location or "Remoto Mundial",
            remote=remote,
            url=link,
            description=combined_desc[:3000],
            requirements=tag_str,
            source="remotive",
            salary_range=salary,
        )
