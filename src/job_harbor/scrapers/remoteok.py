"""RemoteOK scraper — remote jobs worldwide, LATAM-friendly."""

import time
import re
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from .base import Scraper
from ..model import Job


REMOTEOK_URL = "https://remoteok.com"
SEARCH_URL = f"{REMOTEOK_URL}/remote-dev-jobs"


class RemoteOKScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 20) -> list[Job]:
        jobs: list[Job] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="en-US",
            )
            page = context.new_page()

            try:
                url = SEARCH_URL
                if query:
                    url += f"?q={query.replace(' ', '%20')}"
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                rows = page.locator("tr.job").all()
                if not rows:
                    rows = page.locator('[data-tn-component="job"], [itemtype*="Job"]').all()

                for row in rows[:limit]:
                    try:
                        title_el = row.locator("td:first-child a, h2 a, [class*='title'] a").first
                        title = title_el.text_content(timeout=3000) or ""
                        if not title or len(title) < 3:
                            continue

                        href = title_el.get_attribute("href") or ""
                        full_url = href if href.startswith("http") else f"{REMOTEOK_URL}{href}"

                        body = row.text_content(timeout=2000) or ""
                        lines = [l.strip() for l in body.split("\n") if l.strip()]

                        company = ""
                        for l in lines:
                            if l != title and 2 < len(l) < 60 and not company:
                                company = l
                                break

                        salary = ""
                        salary_match = re.search(r'[\$€£][0-9,]+K?[\s-]*[\$€£]?[0-9,]+K?', body)
                        if salary_match:
                            salary = salary_match.group(0)

                        jobs.append(Job(
                            title=title.strip(),
                            company=company.strip() or "Sin especificar",
                            location="Remoto Mundial",
                            remote=True,
                            url=full_url,
                            description=body.strip(),
                            source="remoteok",
                            salary_range=salary,
                        ))
                    except Exception:
                        continue

            except PWTimeout:
                pass
            except Exception:
                pass
            finally:
                browser.close()

        return jobs
