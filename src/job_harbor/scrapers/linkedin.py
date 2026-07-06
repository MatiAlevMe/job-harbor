"""LinkedIn scraper — uses the public guest jobs search API (no auth required).

Searches Chile and Remote locations for tech roles. Parses the HTML
search results for job title, company, location and URL. Optionally
fetches individual job detail pages for the full description.
"""

from typing import Optional

import requests
from bs4 import BeautifulSoup

from .base import Scraper
from ..model import Job


SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

QUERIES = [
    ("developer", "Chile"),
    ("engineer", "Chile"),
    ("qa automation", "Chile"),
    ("backend", "Chile"),
    ("full stack", "Chile"),
    ("developer", "Remote"),
    ("engineer", "Remote"),
    ("qa automation", "Remote"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
}

TECH_KEYWORDS = [
    "engineer", "developer", "programmer", "software",
    "full stack", "fullstack", "backend", "back-end", "frontend", "front-end",
    "devops", "data", "qa", "test", "automation", "python",
    "java", "javascript", "ruby", "rails", "react", "node",
    "cloud", "ml", "ai", "machine learning", "sdet",
]


class LinkedInScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        jobs: list[Job] = []
        seen_urls = set()

        search_specs = [(query, "Chile")] if query else QUERIES

        for q, loc in search_specs:
            if len(jobs) >= limit:
                break
            try:
                page_jobs = self._search(q, loc, limit - len(jobs))
                for job in page_jobs:
                    if job.url not in seen_urls:
                        seen_urls.add(job.url)
                        jobs.append(job)
            except Exception:
                continue

        return jobs[:limit]

    def _search(self, query: str, location: str, limit: int) -> list[Job]:
        jobs: list[Job] = []
        start = 0
        is_remote_search = location.lower() == "remote"

        while len(jobs) < limit and start < 100:
            resp = requests.get(
                SEARCH_URL,
                params={
                    "keywords": query,
                    "location": location,
                    "start": start,
                    "f_WT": 2 if is_remote_search else None,
                },
                headers=HEADERS,
                timeout=20,
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.base-search-card")

            if not cards:
                break

            for card in cards:
                if len(jobs) >= limit:
                    break
                job = self._parse_card(card, is_remote_search)
                if job:
                    jobs.append(job)

            start += 25

        return jobs

    def _parse_card(self, card, is_remote_search: bool = False) -> Optional[Job]:
        title_el = card.select_one("h3.base-search-card__title")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        company_el = card.select_one("h4.base-search-card__subtitle a")
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one("span.job-search-card__location")
        location = location_el.get_text(strip=True) if location_el else ""

        link_el = card.select_one("a.base-card__full-link")
        if not link_el:
            link_el = card.find("a", href=lambda h: h and "jobs/view/" in h)
        url = link_el["href"] if link_el and link_el.get("href") else ""
        if not url:
            return None

        title_lower = title.lower()
        if not any(k in title_lower for k in TECH_KEYWORDS):
            return None

        location_lower = location.lower()
        is_remote = (
            is_remote_search
            or "remoto" in location_lower
            or "remote" in location_lower
            or location_lower.strip() in ("worldwide", "anywhere", "global")
        )

        return Job(
            title=title,
            company=company or "Sin especificar",
            location=location or "Chile",
            remote=is_remote,
            url=url,
            description=f"{title} {company} {location}".strip()[:1000],
            source="linkedin",
        )
