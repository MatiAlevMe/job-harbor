from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Profile:
    name: str = ""
    title: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: float = 0.0
    education: str = ""
    projects: list[str] = field(default_factory=list)
    preferred_roles: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    raw_text: str = ""
    resume_variants: dict[str, str] = field(default_factory=dict)


@dataclass
class Job:
    title: str
    company: str
    location: str
    remote: bool = False
    url: str = ""
    description: str = ""
    requirements: list[str] = field(default_factory=list)
    source: str = ""
    salary_range: Optional[str] = None
    posted_date: Optional[str] = None
    match_score: float = 0.0
    match_reason: str = ""
    skill_matches: list[str] = field(default_factory=list)
    skill_gaps: list[str] = field(default_factory=list)
