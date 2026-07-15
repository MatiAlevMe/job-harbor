"""Jooble scraper — uses the public API (free API key required)."""

import os
import re
from typing import Optional

import requests

from .base import Scraper
from ..model import Job


API_URL = "https://cl.jooble.org/api/{}"

SEARCH_QUERIES = [
    "full stack developer",
    "QA automation engineer",
    "backend engineer",
    "software engineer",
    "Python developer",
    "Ruby on Rails developer",
    "data scientist",
    "devops engineer",
    "frontend developer",
]

NON_TECH_TITLE_WORDS = [
    "writer", "writing", "content", "copywriter", "editor",
    "sales", "marketing", "hr", "recruiter",
    "customer support", "medical", "nurse", "teacher",
    "accountant", "finance", "legal", "driver", "delivery",
]


class JoobleScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        api_key = os.environ.get("JOOBLE_API_KEY", "")
        if not api_key:
            return []

        jobs: list[Job] = []
        seen_ids: set[str] = set()

        queries = [query] if query else SEARCH_QUERIES
        per_query = max(3, limit // len(queries) + 1) if not query else limit

        for q in queries:
            if len(jobs) >= limit:
                break
            try:
                resp = requests.post(
                    API_URL.format(api_key),
                    json={"keywords": q, "location": ""},
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data.get("jobs", [])

                collected = 0
                for entry in raw:
                    if collected >= per_query or len(jobs) >= limit:
                        break
                    job_id = str(entry.get("id", ""))
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    job = self._parse_job(entry)
                    if job:
                        jobs.append(job)
                        collected += 1

            except Exception:
                continue

        return jobs

    def _parse_job(self, entry: dict) -> Optional[Job]:
        title = (entry.get("title") or "").strip()
        company = (entry.get("company") or "").strip()
        link = (entry.get("link") or "").strip()
        location = (entry.get("location") or "").strip()
        salary = (entry.get("salary") or "").strip()
        snippet = (entry.get("snippet") or "").strip()
        source = (entry.get("source") or "").strip()
        job_type = (entry.get("type") or "").strip()

        if not title or not link:
            return None

        title_lower = title.lower()
        if any(w in title_lower for w in NON_TECH_TITLE_WORDS):
            return None

        remote = "remote" in location.lower() or "remoto" in location.lower()
        if not remote:
            remote = "remote" in title_lower or "remoto" in title_lower

        # Clean HTML from snippet
        clean_desc = re.sub(r'<[^>]+>', '', snippet)
        clean_desc = clean_desc.replace('&nbsp;', ' ').replace('\r', ' ').strip()
        combined_desc = f"{title} {company} {source} {clean_desc}".strip()

        posted_date = (entry.get("updated") or "").strip()[:10]

        return Job(
            title=title,
            company=company or "Sin especificar",
            location=location or "Sin especificar",
            remote=remote,
            url=link,
            description=combined_desc[:3000],
            source="jooble",
            salary_range=salary,
            posted_date=posted_date or None,
        )
