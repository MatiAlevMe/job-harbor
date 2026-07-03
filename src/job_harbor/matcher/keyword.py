"""Keyword-based matcher."""

from typing import Optional

from ..model import Profile, Job


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
            if skill_lower in job_text or skill_lower in reqs_text:
                skills_found.append(skill)
            else:
                skills_missing.append(skill)

        title_words = self.profile.title.lower().split()
        role_match = any(w in job_text for w in title_words if len(w) > 3)

        pref_role_match = any(
            role.lower() in job_text for role in self.profile.preferred_roles
        )

        location_ok = any(
            loc.lower() in job_text or (
                loc == "Remoto Chile" and ("remoto" in job_text and "chile" in job_text)
            )
            for loc in self.profile.locations
        )

        total_skills = len(self.profile.skills)
        matched_count = len(skills_found)
        if total_skills == 0:
            skill_score = 0
        elif matched_count >= total_skills * 0.5:
            skill_score = 40
        elif matched_count >= total_skills * 0.3:
            skill_score = 30
        elif matched_count >= total_skills * 0.15:
            skill_score = 20
        elif matched_count > 0:
            skill_score = 15
        else:
            skill_score = 0

        role_score = 25 if role_match or pref_role_match else 0
        location_score = 15 if location_ok else 0

        title_keywords_score = 0
        job_title_lower = job.title.lower()
        profile_roles_lower = [r.lower() for r in self.profile.preferred_roles]
        for role in profile_roles_lower:
            role_words = role.split()
            if any(w in job_title_lower for w in role_words if len(w) > 2):
                title_keywords_score = 10
                break

        total_score = min(100, round(skill_score + role_score + location_score + title_keywords_score))

        reason_parts = []
        if skills_found:
            reason_parts.append(f"Skills: {', '.join(skills_found[:5])}")
            reason_parts.append(f"Match: {matched_count}/{total_skills}")
        if location_ok:
            reason_parts.append("Location OK")
        if role_match or pref_role_match:
            reason_parts.append("Rol coincide")
        reason = " | ".join(reason_parts) if reason_parts else "General match"

        return total_score, reason, skills_found, skills_missing
