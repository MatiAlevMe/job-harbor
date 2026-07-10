"""Keyword-based matcher with word-boundary matching and continuous scoring."""

import datetime
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

LOCATION_COUNTRY_RE = re.compile(
    r"\b(?:"
    # English / native names
    r"usa|u\.s\.a\.?|united states(?: of america)?|estados unidos|"
    r"uk|u\.k\.|united kingdom|great britain|reino unido|"
    r"germany|deutschland|alemania|france|francia|spain|españa|italy|italia|"
    r"netherlands|holland|"
    r"portugal|belgium|austria|switzerland|sweden|norway|denmark|finland|"
    r"ireland|poland|polonia|czech(?:ia| republic)?|hungary|romania|bulgaria|croatia|"
    r"slovakia|slovenia|greece|turkey|turquía|ukraine|russia|rusia|luxembourg|"
    r"malta|cyprus|iceland|"
    r"canada|mexico|méxico|brazil|brasil|"
    r"australia|japan|japón|singapore|india|china|south\s+korea|taiwan|"
    r"vietnam|thailand|indonesia|philippines|malaysia|"
    r"israel|uae|united\s+arab\s+emirates|saudi\s+arabia|qatar|"
    r"new\s+zealand|"
    r"south\s+africa|nigeria|kenya|egypt|egipto|morocco|marruecos"
    r")\b", re.IGNORECASE
)

GEO_RESTRICTION_RE = re.compile(
    r"\b(?:"
    r"must\s+be\s+(?:located|based|resident|domiciled|living)\s+(?:in|within)|"
    r"authorized\s+to\s+work|work\s+authorization|"
    r"citizenship\s+required|permanent\s+resident|"
    r"only\s+(?:for|in|from|open\s+to)\s+(?:residents|candidates|citizens|people|applicants)?|"
    r"limited\s+to|restricted\s+to|"
    r"requires\s+(?:being|living|working|residing)\s+(?:in|within)|"
    r"not\s+(?:open\s+to|available\s+(?:for|to))\s+(?:international|candidates?\s+(?:from|outside))|"
    r"us\s+(?:only|based)\b|united\s+states\s+(?:only|based)\b|usa\s+(?:only|based)\b|"
    r"(?:est|pst|cst|mst|eastern|pacific|central|mountain)\s+time\b"
    r")\b", re.IGNORECASE
)


def _word_boundary(term: str) -> str:
    return r"(?<![a-záéíóúñüç])" + re.escape(term) + r"(?![a-záéíóúñüç])"

SALARY_K_RE = re.compile(r"(\d+)(?:\.?\d*)?k", re.IGNORECASE)


def _parse_salary_to_monthly_usd(salary_range: Optional[str]) -> Optional[float]:
    if not salary_range:
        return None
    text = salary_range.strip()
    if not text:
        return None

    text_lower = text.lower()

    is_clp = bool(re.search(r"clp", text_lower))
    is_hourly = bool(re.search(r"(?:/hr|/hour|por hora|/h\b)", text_lower))
    is_yearly = bool(re.search(r"(?:/yr|/year|/año|anual|per year|per annum|/a\b)", text_lower))

    all_nums = []
    for token in re.findall(r"\d[\d,]*(?:\.\d+)?k?", text_lower):
        try:
            val = token.lower()
            if val.endswith("k"):
                val_num = float(val[:-1].replace(",", "")) * 1000
            else:
                val_num = float(val.replace(",", ""))
            all_nums.append(val_num)
        except ValueError:
            continue

    if not all_nums:
        return None

    avg = sum(all_nums) / len(all_nums)
    monthly = avg

    if is_hourly:
        monthly *= 160
    elif is_yearly:
        monthly /= 12.0
    elif is_clp:
        monthly /= 850.0
    elif avg < 20000:
        pass
    else:
        monthly /= 12.0

    return round(monthly, 0)


def _calc_salary_bonus(salary_range: Optional[str]) -> int:
    monthly = _parse_salary_to_monthly_usd(salary_range)
    if monthly is None:
        return 0
    if monthly >= 3000:
        return 8
    if monthly >= 2000:
        return 5
    if monthly >= 1000:
        return 3
    return 0


def _calc_recency_bonus(posted_date: Optional[str]) -> tuple[int, int]:
    if not posted_date:
        return 0, 999
    try:
        dt = datetime.datetime.strptime(posted_date[:10], "%Y-%m-%d")
        days_ago = (datetime.datetime.now() - dt).days
    except (ValueError, TypeError):
        return 0, 999
    if days_ago <= 3:
        return 10, days_ago
    if days_ago <= 7:
        return 5, days_ago
    if days_ago <= 14:
        return 3, days_ago
    return 0, days_ago


class KeywordMatcher:
    def __init__(self, profile: Profile):
        self.profile = profile

    @staticmethod
    def _calc_location_tier(job: Job) -> tuple[int, str]:
        job_loc = (job.location or "").lower()
        search_text = f"{job.title} {job.company} {job.description} {job_loc}".lower()

        is_remote = job.remote or bool(re.search(r"\b(?:remote|remoto|worldwide|anywhere)\b", job_loc))
        is_hybrid = bool(re.search(r"\b(?:h[ií]brido|hibrido|hybrid|mixed)\b", search_text))
        if not is_hybrid:
            has_presencial = bool(re.search(r"\bpresencial\b", job_loc))
            has_remoto_word = bool(re.search(r"\bremoto\b", job_loc))
            is_hybrid = has_presencial and has_remoto_word

        in_valpo = bool(re.search(r"\b(?:reñaca|viña\s*del\s*mar|valpara[íi]so)\b", search_text))
        in_santiago = bool(re.search(r"\bsantiago\b", search_text))
        in_chile = bool(re.search(r"\bchile\b", search_text))

        geo_restricted = bool(LOCATION_COUNTRY_RE.search(job_loc))
        if not geo_restricted:
            geo_restricted = bool(LOCATION_COUNTRY_RE.search(search_text))
        if not geo_restricted:
            geo_restricted = bool(GEO_RESTRICTION_RE.search(search_text))

        if is_hybrid:
            if in_valpo:
                return 10, "Híbrido Valparaíso"
            if in_santiago:
                return 5, "Híbrido Santiago"
            if in_chile:
                return 1, "Híbrido Chile"
            return 5, "Híbrido"
        if is_remote:
            if in_chile:
                return 13, "Remoto Chile"
            if not geo_restricted:
                return 15, "Remoto Mundial"
            return 5, "Remoto Restringido"
        if in_valpo:
            return 8, "Presencial Valparaíso"
        if in_santiago:
            return 3, "Presencial Santiago"
        if in_chile:
            return -2, "Presencial Chile"
        if geo_restricted:
            return -15, "Restringido"
        return 0, "Sin match"

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
        if required_years > 0:
            gap = required_years - self.profile.experience_years
            if gap > 0:
                exp_gap_penalty = min(15, round(gap * 3))
                seniority_penalty += exp_gap_penalty

        # Junior bonus
        if JUNIOR_RE.search(title_lower):
            seniority_penalty -= 5

        # --- Location tier ---
        location_score, location_tag = self._calc_location_tier(job)

        # --- Scores ---
        total_skills = len(self.profile.skills)
        matched_count = len(skills_found)
        if total_skills == 0 or matched_count == 0:
            skill_score = 0
        else:
            half = max(1, round(total_skills * 0.5))
            skill_score = round(15 + 25 * min(1.0, matched_count / half))

        role_score = 25 if role_match else 0

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

        salary_bonus = _calc_salary_bonus(job.salary_range)
        recency_bonus, days_ago = _calc_recency_bonus(job.posted_date)

        total_score = min(100, max(0, round(
            skill_score + role_score + location_score + title_keywords_score
            + salary_bonus + recency_bonus
            - seniority_penalty
        )))

        # --- Reason ---
        reason_parts = []
        if skills_found:
            reason_parts.append(f"Skills: {', '.join(skills_found[:5])}")
            reason_parts.append(f"Match: {matched_count}/{total_skills}")
        if location_tag != "Sin match":
            reason_parts.append(location_tag)
        if role_match:
            reason_parts.append("Rol coincide")
        if has_senior_title:
            reason_parts.append(f"+Senior({seniority_penalty})")
        if exp_gap_penalty > 0:
            reason_parts.append(f"+{required_years}a exp")
        if JUNIOR_RE.search(title_lower):
            reason_parts.append("-Junior")
        if salary_bonus:
            reason_parts.append(f"+Salario({salary_bonus})")
        if recency_bonus:
            reason_parts.append(f"+Reciente({days_ago}d)")
        reason = " | ".join(reason_parts) if reason_parts else "General match"

        return total_score, reason, skills_found, skills_missing
