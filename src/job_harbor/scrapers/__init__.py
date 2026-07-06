from .base import Scraper
from .remoteok import RemoteOKScraper
from .himalayas import HimalayasScraper
from .remotive import RemotiveScraper
from .getonboard import GetOnBoardScraper
from .vacantes_digitales import VacantesDigitalesScraper
from .jooble import JoobleScraper
from .linkedin import LinkedInScraper

__all__ = [
    "Scraper",
    "RemoteOKScraper",
    "HimalayasScraper",
    "RemotiveScraper",
    "GetOnBoardScraper",
    "VacantesDigitalesScraper",
    "JoobleScraper",
    "LinkedInScraper",
]
