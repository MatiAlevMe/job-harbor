"""Keyword-based matcher using TF-IDF + cosine similarity."""

import re
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..model import Profile, Job


class KeywordMatcher:
    def __init__(self, profile: Profile):
        self.profile = profile
        self._build_profile_vector()

    def _build_profile_vector(self):
        profile_text = " ".join([
            self.profile.title or "",
            " ".join(self.profile.skills),
            " ".join(self.profile.preferred_roles),
            " ".join(self.profile.projects),
        ])
        self.profile_text = profile_text.lower()

    def match(self, job: Job) -> tuple[float, str, list[str], list[str]]:
        job_text = f"{job.title} {job.company} {job.description}".lower()

        skills_found = []
        skills_missing = []

        for skill in self.profile.skills:
            if skill.lower() in job_text:
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

        vectors = TfidfVectorizer(stop_words="spanish", max_features=500)
        try:
            tfidf = vectors.fit_transform([self.profile_text, job_text])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        except Exception:
            sim = 0.0

        skill_score = len(skills_found) / max(len(self.profile.skills), 1) * 40
        role_score = 20 if role_match or pref_role_match else 0
        location_score = 15 if location_ok else 0
        sim_score = sim * 25

        total_score = min(100, round(skill_score + role_score + location_score + sim_score))

        reason_parts = []
        if skills_found:
            reason_parts.append(f"Skills: {', '.join(skills_found[:5])}")
        if skills_missing:
            reason_parts.append(f"Gaps: {', '.join(skills_missing[:5])}")
        if location_ok:
            reason_parts.append("Location OK")
        reason = " | ".join(reason_parts) if reason_parts else "General match"

        return total_score, reason, skills_found, skills_missing
