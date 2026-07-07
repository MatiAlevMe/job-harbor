"""Himalayas.app scraper — uses the public JSON API (no auth required)."""

import re
import requests
from typing import Optional

from .base import Scraper
from ..model import Job


API_URL = "https://himalayas.app/jobs/api"

TECH_CATEGORY_FILTERS = [
    "backend", "frontend", "fullstack", "full-stack", "full stack",
    "software", "engineer", "developer", "devops", "sre",
    "data", "ml", "machine-learning", "ai", "artificial-intelligence",
    "qa", "test", "automation", "quality",
    "python", "javascript", "typescript", "ruby", "rails", "java",
    "react", "node", "golang", "rust",
    "cloud", "infrastructure", "platform",
    "mobile", "ios", "android",
    "security", "cyber",
]


class HimalayasScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        jobs: list[Job] = []
        page = 0

        try:
            while len(jobs) < limit:
                resp = requests.get(
                    API_URL,
                    params={"limit": 50, "offset": page * 50},
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
                if not raw:
                    break

                for entry in raw:
                    if len(jobs) >= limit:
                        break
                    job = self._parse_job(entry)
                    if job:
                        jobs.append(job)

                page += 1
                if len(raw) < 50:
                    break

        except Exception:
            pass

        return jobs

    def _parse_job(self, entry: dict) -> Optional[Job]:
        title = (entry.get("title") or "").strip()
        company = (entry.get("companyName") or "").strip()
        link = (entry.get("applicationLink") or "").strip()
        description = (entry.get("description") or "")
        categories = entry.get("categories") or []
        loc_restrictions = entry.get("locationRestrictions") or []
        remote = bool(entry.get("remote"))
        salary_min = entry.get("minSalary")
        salary_max = entry.get("maxSalary")
        seniority = entry.get("seniority") or []

        if not title or not link or not company:
            return None

        if not self._is_tech_job(title, categories):
            return None

        location = ", ".join(loc_restrictions) if loc_restrictions else "Remoto Mundial"
        salary_str = ""
        if salary_min or salary_max:
            parts = []
            if salary_min:
                parts.append(f"${salary_min}")
            if salary_max:
                parts.append(f"${salary_max}")
            salary_str = " - ".join(parts)

        tag_str = ", ".join(categories) if categories else ""
        combined_desc = f"{title} {company} {tag_str} {description}".strip()

        raw_date = entry.get("pub_date", "") or ""
        posted_date = raw_date[:10] if raw_date else None

        return Job(
            title=title,
            company=company,
            location=location,
            remote=remote,
            url=link,
            description=combined_desc,
            source="himalayas",
            salary_range=salary_str,
            posted_date=posted_date,
        )

    def _is_tech_job(self, title: str, categories: list[str]) -> bool:
        text = f"{title} {' '.join(categories)}".lower()
        for kw in TECH_CATEGORY_FILTERS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return True
        return False
