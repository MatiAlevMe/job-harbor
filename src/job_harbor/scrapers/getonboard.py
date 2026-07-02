"""GetOnBoard scraper — Chilean tech job portal."""

import time
import re
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from .base import Scraper
from ..model import Job


GETONBOARD_URL = "https://www.getonbrd.com"
SEARCH_URL = f"{GETONBOARD_URL}/empleos/desarrollo-y-programacion"


class GetOnBoardScraper(Scraper):
    def scrape(self, query: Optional[str] = None, limit: int = 30) -> list[Job]:
        jobs: list[Job] = []

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

            try:
                url = SEARCH_URL
                if query:
                    url += f"?q={query.replace(' ', '%20')}"
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                cards = page.locator('[data-company], article, [class*="job"], [class*="card"]').all()
                if not cards:
                    cards = page.locator("a[href*='/empleos/']").all()

                seen_urls = set()
                for card in cards[:limit]:
                    try:
                        link = card
                        href = ""
                        tag = link.tag_name
                        if tag != "a":
                            link = card.locator("a[href*='/empleos/']").first
                            href = link.get_attribute("href") or ""
                        else:
                            href = link.get_attribute("href") or ""

                        if not href or href in seen_urls:
                            continue
                        full_url = href if href.startswith("http") else f"{GETONBOARD_URL}{href}"
                        seen_urls.add(full_url)

                        title = link.text_content(timeout=2000) or ""
                        if not title or len(title) < 5:
                            continue

                        body = card.text_content(timeout=2000) or ""
                        lines = [l.strip() for l in body.split("\n") if l.strip()]

                        company = ""
                        location = ""
                        for l in lines:
                            if l != title and len(l) > 2 and not company:
                                company = l
                            if "remoto" in l.lower() or "santiago" in l.lower() or "chile" in l.lower():
                                location = location or l

                        remote = "remoto" in body.lower()

                        jobs.append(Job(
                            title=title.strip(),
                            company=company.strip() or "Sin especificar",
                            location=location.strip() or "Chile",
                            remote=remote,
                            url=full_url,
                            description=body.strip(),
                            source="getonboard",
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
