"""Base scraper interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..model import Job


class Scraper(ABC):
    """Abstract base class for job scrapers."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.name = self.__class__.__name__.replace("Scraper", "").lower()

    @abstractmethod
    def scrape(self, query: Optional[str] = None, limit: int = 30) -> list[Job]:
        """Scrape job listings from the source."""
        ...
