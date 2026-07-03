"""RemoteOK scraper — uses the official JSON API (no Playwright)."""

import re
import requests
from typing import Optional

from .base import Scraper
from ..model import Job


API_URL = "https://remoteok.com/api"

TITLE_TECH_KEYWORDS = [
    r"\bengineer\b", r"\bdeveloper\b", r"\bprogrammer\b", r"\bsoftware\b",
    r"\bfull.?stack\b", r"\bbackend\b", r"\bfrontend\b", r"\bdevops\b",
    r"\bsre\b", r"\bdata\s+(scientist|engineer|analyst)\b",
    r"\bml.?ops\b", r"\bmachine learning\b",
    r"\bai\b", r"\bqa\b", r"\bautomation\b", r"\btest\s+(engineer|developer|automation)\b",
    r"\bruby\b", r"\brails\b", r"\bpython\b", r"\bjava\b", r"\breact\b",
    r"\bnode\b", r"\bcloud\s+(engineer|architect)\b",
    r"\bsolutions? architect\b", r"\bdata scientist\b",
]

TITLE_NON_TECH_KEYWORDS = [
    r"\bvice president\b", r"\bvp\b", r"\bpresident\b",
    r"\bdirector\b", r"\bcoordinator\b", r"\bassistant\b",
    r"\bspecialist\b", r"\brepresentative\b", r"\bassociate\b",
    r"\bexecutive\b", r"\bmanager\b",
    r"\bdriver\b", r"\brecruiter\b", r"\bproofreader\b",
    r"\beditor\b", r"\bwriter\b", r"\bsocial media\b",
    r"\bmarketing\b", r"\bsales\b", r"\bhr\b",
    r"\btutor\b", r"\bprofesor\b", r"\bteacher\b",
    r"\bcarer\b", r"\bsupport\b", r"\boperator\b",
    r"\bdriver\b", r"\bcrew\b", r"\brestoration\b",
    r"\bregistrar\b", r"\btrader\b", r"\bcrypto\b",
    r"\bclinical\b", r"\bnurse\b", r"\bpatient\b",
    r"\bdriver\b", r"\bmobiliser\b",
    r"\borientador\b", r"\binstructor\b", r"\bcoach\b",
    r"\bcounselor\b", r"\bcareer\b",
]

SPECIFIC_TECH_TAGS = {
    "python", "javascript", "typescript", "ruby", "rails", "react",
    "node", "golang", "rust", "swift", "java", "sql",
    "full stack", "front end", "backend", "data science",
    "qa", "testing", "devops", "cloud", "mobile", "game dev",
    "ai", "ml", "blockchain", "embedded",
}

NON_TECH_TAGS = {
    "sales", "marketing", "hr", "recruiter", "legal",
    "coordinator", "bus dev", "copywriting", "writer",
    "english teacher", "finance", "medical",
    "customer support", "virtual assistant", "non tech",
}


def _is_tech_job(job: dict) -> bool:
    tags = [t.lower() for t in job.get("tags", []) if isinstance(t, str)]
    position = (job.get("position", "") or "").lower()

    title_is_tech = any(re.search(ptn, position) for ptn in TITLE_TECH_KEYWORDS)
    title_is_non_tech = any(re.search(ptn, position) for ptn in TITLE_NON_TECH_KEYWORDS)
    has_specific_tech_tag = any(t in SPECIFIC_TECH_TAGS for t in tags)
    has_non_tech_tag = any(t in NON_TECH_TAGS for t in tags)

    if title_is_non_tech:
        return False
    if title_is_tech:
        return True
    if has_specific_tech_tag and not has_non_tech_tag:
        tags_without_broad = [t for t in tags if t not in {"dev", "web dev", "technical", "engineering", "full time", "junior", "senior", "digital nomad"}]
        specific_tags = [t for t in tags_without_broad if t in SPECIFIC_TECH_TAGS]
        if len(specific_tags) >= 2:
            return True
    return False


class RemoteOKScraper(Scraper):
    def __init__(self):
        super().__init__()
        self.headless = True

    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        jobs: list[Job] = []

        try:
            resp = requests.get(API_URL, headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            }, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return jobs

        # data[0] is metadata, actual jobs start at index 1
        raw_jobs = data[1:] if isinstance(data, list) and len(data) > 1 else []

        for entry in raw_jobs:
            if not _is_tech_job(entry):
                continue
            if len(jobs) >= limit:
                break

            position = entry.get("position", "") or ""
            company = entry.get("company", "") or ""
            location = entry.get("location", "") or "Remote"
            tags = entry.get("tags", []) or []
            description = entry.get("description", "") or ""
            salary_min = entry.get("salary_min")
            salary_max = entry.get("salary_max")
            url = entry.get("url", "") or entry.get("apply_url", "") or ""

            salary_range = ""
            if salary_min or salary_max:
                parts = []
                if salary_min:
                    parts.append(f"${salary_min}")
                if salary_max:
                    parts.append(f"${salary_max}")
                salary_range = " - ".join(parts)

            remote = "remote" in location.lower() or "remote" in str(tags).lower()
            tag_str = ", ".join(tags) if tags else ""

            combined_desc = f"{position} {company} {tag_str} {description}".strip()

            jobs.append(Job(
                title=position.strip(),
                company=company.strip() or "Sin especificar",
                location=location.strip() or "Remoto Mundial",
                remote=remote,
                url=url.strip(),
                description=combined_desc,
                requirements=tag_str,
                source="remoteok",
                salary_range=salary_range,
            ))

        return jobs
