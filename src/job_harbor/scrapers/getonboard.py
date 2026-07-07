"""GetOnBoard scraper — uses the public RSS feed (no Playwright, no auth)."""

import re
import xml.etree.ElementTree as ET
from typing import Optional

import requests

from .base import Scraper
from ..model import Job


RSS_URL = "https://www.getonbrd.com/jobs/feed"

TECH_CATEGORIES = {
    "Programming",
    "Data Science / Analytics",
    "DevOps / Sysadmin",
    "Quality Assurance (QA)",
    "UX / UI",
    "Product Management",
    "Project Management",
    "Mobile",
    "Security",
    "Machine Learning",
}

NON_TECH_CATEGORIES = {
    "Marketing",
    "Sales",
    "Administration",
    "Finance",
    "Human Resources",
    "Customer Support",
    "Legal",
    "Design / Creative",
    "Content / Writing",
}


class GetOnBoardScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        jobs: list[Job] = []

        try:
            resp = requests.get(
                RSS_URL,
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

            root = ET.fromstring(resp.content)
            for job_elem in root.findall("job"):
                if len(jobs) >= limit:
                    break
                job = self._parse_job(job_elem)
                if job:
                    jobs.append(job)

        except Exception:
            pass

        return jobs

    def _parse_job(self, elem: ET.Element) -> Optional[Job]:
        def get(tag: str) -> str:
            el = elem.find(tag)
            return (el.text or "").strip() if el is not None else ""

        title = get("title")
        company = get("company")
        url = get("url")
        category = get("category")
        experience = get("experience")
        country = get("country")
        salary_text = get("salary")
        jobtype = get("jobtype") or get("working_hours") or ""
        description_raw = get("description")

        if not title or not url or not company:
            return None

        if category in NON_TECH_CATEGORIES:
            return None

        if category not in TECH_CATEGORIES:
            title_lower = title.lower()
            tech_words = [
                "engineer", "developer", "programmer", "software",
                "full stack", "backend", "frontend", "devops",
                "data", "qa", "test", "automation", "python",
                "java", "javascript", "ruby", "rails", "react",
                "node", "cloud", "ml", "ai", "machine learning",
            ]
            if not any(w in title_lower for w in tech_words):
                return None

        location = country or "Chile"
        remote = "remoto" in title.lower() or "remote" in title.lower()
        if not remote:
            location_lower = (location + " " + title).lower()
            remote = ("remoto" in location_lower or "remote" in location_lower)

        raw_date = get("pubdate") or get("date") or ""
        posted_date = raw_date[:10] if raw_date else None

        combined_desc = f"{title} {company} {category} {experience} {description_raw}".strip()

        return Job(
            title=title,
            company=company,
            location=location,
            remote=remote,
            url=url,
            description=combined_desc[:3000],
            source="getonboard",
            salary_range=salary_text,
            posted_date=posted_date,
        )
