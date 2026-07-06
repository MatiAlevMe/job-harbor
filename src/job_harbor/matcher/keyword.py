"""Keyword-based matcher with word-boundary matching and continuous scoring."""

import re
from typing import Optional

from ..model import Profile, Job


def _word_boundary(term: str) -> str:
    return r"(?<![a-záéíóúñ])" + re.escape(term) + r"(?![a-záéíóúñ])"


class KeywordMatcher:
    def __init__(self, profile: Profile):
        self.profile = profile

    def match(self, job: Job) -> tuple[float, str, list[str], list[str]]:
        job_text = f"{job.title} {job.company} {job.description}".lower()
        reqs_text = (job.requirements or "").lower()

        skills_found = []
        skills_missing = []

        for skill in self.profile.skills:
            skill_lower = skill.lower()
            pattern = _word_boundary(skill_lower)
            if re.search(pattern, job_text) or re.search(pattern, reqs_text):
                skills_found.append(skill)
            else:
                skills_missing.append(skill)

        role_keywords = set()
        for w in self.profile.title.lower().split():
            if len(w) > 3:
                role_keywords.add(w)
        for r in self.profile.preferred_roles:
            for w in r.lower().split():
                if len(w) > 2:
                    role_keywords.add(w)

        role_match = False
        for kw in role_keywords:
            pattern = _word_boundary(kw)
            if re.search(pattern, job_text):
                role_match = True
                break

        location_ok = False
        for loc in self.profile.locations:
            if loc == "Remoto Chile":
                if re.search(r"remoto", job_text) and re.search(r"chile", job_text):
                    location_ok = True
                    break
            else:
                pattern = _word_boundary(loc.lower())
                if re.search(pattern, job_text):
                    location_ok = True
                    break

        total_skills = len(self.profile.skills)
        matched_count = len(skills_found)
        if total_skills == 0 or matched_count == 0:
            skill_score = 0
        else:
            half = max(1, round(total_skills * 0.5))
            skill_score = round(15 + 25 * min(1.0, matched_count / half))

        role_score = 25 if role_match else 0
        location_score = 15 if location_ok else 0

        title_keywords_score = 0
        job_title_lower = job.title.lower()
        for role in self.profile.preferred_roles:
            for w in role.lower().split():
                if len(w) > 2:
                    pattern = _word_boundary(w)
                    if re.search(pattern, job_title_lower):
                        title_keywords_score = 10
                        break
            if title_keywords_score:
                break

        total_score = min(100, round(skill_score + role_score + location_score + title_keywords_score))

        reason_parts = []
        if skills_found:
            reason_parts.append(f"Skills: {', '.join(skills_found[:5])}")
            reason_parts.append(f"Match: {matched_count}/{total_skills}")
        if location_ok:
            reason_parts.append("Location OK")
        if role_match:
            reason_parts.append("Rol coincide")
        reason = " | ".join(reason_parts) if reason_parts else "General match"

        return total_score, reason, skills_found, skills_missing
