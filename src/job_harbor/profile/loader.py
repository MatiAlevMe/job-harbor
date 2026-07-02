"""Load professional profile from guia-laboral ADOC files."""

import os
import re
from typing import Optional

from ..model import Profile


def _find_repo_path() -> Optional[str]:
    env_path = os.environ.get("GUIA_LABORAL_PATH")
    if env_path and os.path.isdir(env_path):
        return os.path.abspath(env_path)

    candidates = [
        os.path.join("..", "guia-laboral"),
        os.path.join("..", "..", "guia-laboral"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return os.path.abspath(c)
    return None


def _parse_adoc_field(text: str, key: str) -> str:
    pattern = rf"- \*{key}\*: (.+)"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_skills(text: str) -> list[str]:
    skills = set()
    patterns = [
        r"_Stack(?: especializado)?_: (.+)",
        r"Stack: (.+)",
        r"\*Stack\*: (.+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            parts = re.split(r"[,;·|•]", m.group(1))
            for part in parts:
                part = part.strip().rstrip(".")
                if part and len(part) > 1:
                    skills.add(part)
    return sorted(skills)


def _extract_sections(text: str, section_name: str) -> list[str]:
    items = []
    pattern = rf"### {re.escape(section_name)}.*?\n(.*?)(?=\n###|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    if m:
        block = m.group(1)
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("- **") or line.startswith("- "):
                items.append(line.lstrip("- ").strip())
    return items


def load_profile(cv_rel_path: Optional[str] = None) -> Profile:
    repo_path = _find_repo_path()
    if not repo_path:
        return Profile(
            name="Matías Vizancio Alevropulos Erlbaun",
            title="Ingeniero Civil Informático | Full Stack Engineer & QA Automation",
            skills=["Python", "Ruby on Rails", "JavaScript", "SQL", "Selenium",
                    "Cucumber", "Jenkins", "Git", "AWS", "Postman", "MySQL",
                    "Playwright", "CI/CD", "GitOps"],
            experience_years=1.5,
            education="Ingeniero Civil Informático — PUCV (2025)",
            projects=["KineViz", "FireGuard", "MCP Server"],
            preferred_roles=["QA Automation", "Full Stack", "Backend"],
            locations=["Valparaíso", "Santiago", "Remoto Chile", "Remoto Mundial"],
            languages=["Spanish", "English C2"],
        )

    cv_path = cv_rel_path or os.path.join(repo_path, "cv", "cv-es.adoc")
    resume_path = os.path.join(repo_path, "resume", "resume-es.adoc")

    text = ""
    for p in [cv_path, resume_path]:
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                text += f.read() + "\n"

    name = _parse_adoc_field(text, "Name") or "Matías Vizancio Alevropulos Erlbaun"

    title_match = re.search(r"\*{0,2}_?([^*_]+Full Stack[^_]*)_?\*{0,2}", text)
    title = title_match.group(1).strip() if title_match else "Ingeniero Civil Informático"

    skills = _extract_skills(text)
    if not skills:
        skills = ["Python", "Ruby on Rails", "JavaScript", "SQL", "Selenium"]

    experience_years = 1.5

    edu_match = re.search(r"\*\*Ingeniero Civil Informático\*\*.*?\((\d{4})\s*-\s*(\d{4})\)", text)
    education = edu_match.group(0).strip() if edu_match else "Ingeniero Civil Informático — PUCV"

    projects = []
    proj_match = re.findall(r"### ([A-Za-z].*?)\n", text)
    for p in proj_match:
        p = p.strip()
        if p not in ["Sobre Mí", "Información Personal", "Experiencia"]:
            projects.append(p)

    return Profile(
        name=name,
        title=title,
        skills=skills,
        experience_years=experience_years,
        education=education,
        projects=projects[:6],
        preferred_roles=["QA Automation", "Full Stack", "Backend"],
        locations=["Valparaíso", "Santiago", "Remoto Chile", "Remoto Mundial"],
        languages=["Spanish", "English C2"],
    )
