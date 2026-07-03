"""Google Jobs scraper using Playwright (lazy import).

Google Jobs aggregates listings from LinkedIn, Indeed, and many other sources,
giving broad coverage with a single scraper.
"""

import time
import re
import urllib.parse
from typing import Optional

from .base import Scraper
from ..model import Job


def _playwright():
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    return sync_playwright, PWTimeout


SEARCH_QUERIES = [
    "QA Automation Engineer Chile",
    "Full Stack Developer Chile remoto",
    "Backend Engineer remoto Chile",
    "Software Engineer Chile",
    "Python Developer Chile remoto",
    "Ruby on Rails developer Chile",
    "QA Engineer remote Latin America",
    "Data Engineer Chile",
]


class GoogleJobsScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 40) -> list[Job]:
        try:
            sync_playwright, _ = _playwright()
        except ImportError:
            return []

        queries = [query] if query else SEARCH_QUERIES
        all_jobs: dict[str, Job] = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="es-CL",
            )
            page = context.new_page()

            for q in queries:
                try:
                    jobs = self._scrape_query(page, q)
                    for j in jobs:
                        if j.url and j.url not in all_jobs:
                            all_jobs[j.url] = j
                    time.sleep(3)
                except Exception:
                    continue

            browser.close()

        return list(all_jobs.values())[:limit]

    def _scrape_query(self, page, query: str) -> list[Job]:
        jobs: list[Job] = []
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}&ibp=htl;jobs&hl=es"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)

            cards = page.locator("div[role='treeitem']").all()
            if not cards:
                cards = page.locator('[jsname="h3c6df"], [data-hveid]').all()
            if not cards:
                cards = page.locator("li").filter(has=page.locator("a[href*='/jobs']")).all()

            seen_urls = set()
            for card in cards[:15]:
                try:
                    title_el = card.locator('[data-ved], [role="heading"], h3, a').first
                    title = title_el.text_content(timeout=3000) or ""
                    if not title or len(title) < 5:
                        continue

                    link_el = card.locator("a[href*='https']").first
                    href = link_el.get_attribute("href") if link_el else ""
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                    elif not href:
                        continue

                    body_text = card.text_content(timeout=2000) or ""
                    lines = [l.strip() for l in body_text.split("\n") if l.strip()]

                    company = ""
                    location = ""
                    for i, line in enumerate(lines):
                        if line == title and i + 1 < len(lines):
                            company = lines[i + 1]
                        if "Santiago" in line or "Remoto" in line or "Chile" in line:
                            location = location or line

                    remote = "remoto" in body_text.lower() or "remote" in body_text.lower()

                    jobs.append(Job(
                        title=title.strip(),
                        company=company.strip(),
                        location=location.strip() or "Chile",
                        remote=remote,
                        url=href,
                        description=body_text.strip(),
                        source="google_jobs",
                    ))
                except Exception:
                    continue

        except PWTimeout:
            pass
        except Exception:
            pass

        return jobs
