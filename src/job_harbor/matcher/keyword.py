"""Keyword-based matcher with word-boundary matching and continuous scoring."""

import re
from typing import Optional

from ..model import Profile, Job


SENIOR_PATTERNS = [
    (re.compile(r"\bsenior\b", re.IGNORECASE), 20),
    (re.compile(r"\bsr\.?\b", re.IGNORECASE), 20),
    (re.compile(r"\blead\b", re.IGNORECASE), 25),
    (re.compile(r"\bprincipal\b", re.IGNORECASE), 25),
    (re.compile(r"\bstaff\b", re.IGNORECASE), 25),
    (re.compile(r"\barchitect\b", re.IGNORECASE), 25),
    (re.compile(r"\bhead\b", re.IGNORECASE), 30),
    (re.compile(r"\bchief\b", re.IGNORECASE), 30),
    (re.compile(r"\bvp\b", re.IGNORECASE), 30),
    (re.compile(r"\bvice\s+president\b", re.IGNORECASE), 30),
    (re.compile(r"\bdirector\b", re.IGNORECASE), 30),
    (re.compile(r"\bexpert\b", re.IGNORECASE), 20),
]

JUNIOR_RE = re.compile(r"\b(?:junior|jr\.?|trainee|entry|graduate|associate)\b", re.IGNORECASE)

EXP_RE = re.compile(r"(\d+)\+?\s*(?:year|yr|año)s?\s*(?:of\s+)?(?:exp|experience)?", re.IGNORECASE)

RESTRICTED_RE = re.compile(
    r"\b(?:"
    r"usa|u\.s\.a\.?|united states(?: of america)?|"
    r"uk|u\.k\.|united kingdom|great britain|"
    r"germany|deutschland|france|spain|italy|netherlands|holland|"
    r"canada|australia|japan|singapore|"
    r"switzerland|sweden|norway|denmark|finland|ireland|new\s+zealand|"
    r"europe(?:an)?|eu\b|"
    r"must\s+be\s+(?:located|based|resident)\s+in|"
    r"work\s+authorization|citizenship\s+required|authorized\s+to\s+work"
    r")\b", re.IGNORECASE
)


def _word_boundary(term: str) -> str:
    return r"(?<![a-záéíóúñüç])" + re.escape(term) + r"(?![a-záéíóúñüç])"


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

        # --- Role match: only from preferred_roles, on title+company (not description) ---
        title_company_lower = f"{job.title} {job.company}".lower()
        role_match = any(
            re.search(_word_boundary(w), title_company_lower)
            for r in self.profile.preferred_roles
            for w in r.lower().split()
            if len(w) > 2
        )

        # --- Seniority detection ---
        title_lower = job.title.lower()

        seniority_penalty = 0
        has_senior_title = False
        for ptn, penalty in SENIOR_PATTERNS:
            if ptn.search(title_lower):
                seniority_penalty = penalty
                has_senior_title = True
                break

        # Experience requirement in description
        exp_gap_penalty = 0
        exp_match = EXP_RE.search(job_text)
        required_years = int(exp_match.group(1)) if exp_match else 0
        if required_years > 2:
            gap = required_years - self.profile.experience_years
            if gap > 2:
                exp_gap_penalty = min(15, round((gap - 2) * 3))
                seniority_penalty += exp_gap_penalty

        # Junior bonus
        if JUNIOR_RE.search(title_lower):
            seniority_penalty -= 5

        # --- Location matching + geo-restriction ---
        location_ok = False
        job_location_lower = (job.location or "").lower()
        combined_lower = f"{job.title} {job.company} {job.description}".lower()

        is_remote_by_loc = bool(re.search(r"\b(?:remote|remoto|worldwide|anywhere)\b", job_location_lower))
        is_remote_any = job.remote or is_remote_by_loc

        geo_restricted = bool(RESTRICTED_RE.search(job_location_lower))
        if not geo_restricted:
            geo_restricted = bool(RESTRICTED_RE.search(combined_lower))

        for loc in self.profile.locations:
            if loc == "Remoto Chile":
                if (is_remote_any and re.search(r"\bchile\b", job_location_lower, re.IGNORECASE)):
                    location_ok = True
                    break
                if re.search(r"\bremoto\b", combined_lower) and re.search(r"\bchile\b", combined_lower):
                    location_ok = True
                    break
                if re.search(r"\bremote\b", combined_lower) and re.search(r"\bchile\b", combined_lower):
                    location_ok = True
                    break
            elif loc == "Remoto Mundial":
                if is_remote_any and not geo_restricted:
                    location_ok = True
                    break
            else:
                pattern = _word_boundary(loc.lower())
                if re.search(pattern, combined_lower):
                    location_ok = True
                    break

        # --- Scores ---
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
        for role in self.profile.preferred_roles:
            for w in role.lower().split():
                if len(w) > 2:
                    pattern = _word_boundary(w)
                    if re.search(pattern, title_lower):
                        title_keywords_score = 10
                        break
            if title_keywords_score:
                break

        geo_penalty = 15 if geo_restricted else 0

        total_score = min(100, max(0, round(
            skill_score + role_score + location_score + title_keywords_score
            - seniority_penalty - geo_penalty
        )))

        # --- Reason ---
        reason_parts = []
        if skills_found:
            reason_parts.append(f"Skills: {', '.join(skills_found[:5])}")
            reason_parts.append(f"Match: {matched_count}/{total_skills}")
        if location_ok:
            reason_parts.append("Location OK")
        if role_match:
            reason_parts.append("Rol coincide")
        if has_senior_title:
            reason_parts.append(f"+Senior({seniority_penalty})")
        if exp_gap_penalty > 0:
            reason_parts.append(f"+{required_years}a exp")
        if JUNIOR_RE.search(title_lower):
            reason_parts.append("-Junior")
        if geo_restricted:
            reason_parts.append("+Restringido")
        reason = " | ".join(reason_parts) if reason_parts else "General match"

        return total_score, reason, skills_found, skills_missing
