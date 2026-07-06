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
        "guia-laboral",
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


CORE_SKILLS = {
    "Python", "Ruby on Rails", "Ruby", "JavaScript", "TypeScript", "Java",
    "SQL", "React", "Next.js", "Node.js", "Angular", "Vue.js",
    "PostgreSQL", "MySQL", "MongoDB", "SQLite", "NoSQL",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD",
    "Git", "GitHub", "GitLab", "Bitbucket",
    "Selenium", "Cucumber", "Playwright", "Jenkins", "Maven",
    "Postman", "SoapUI", "BrowserStack", "REST APIs", "GraphQL",
    "Machine Learning", "Data Engineering", "ETL", "Pandas",
    "Full Stack", "Backend", "Frontend", "QA Automation",
    "Linux", "Bash", "Shell", "HTML", "CSS",
    "Rails", "Flask", "Django", "FastAPI",
    "Redis", "Kafka", "RabbitMQ", "Nginx",
    "Terraform", "Ansible", "Puppet", "Chef",
    "Prometheus", "Grafana", "Datadog",
    "Jira", "Bootstrap", "Data Science", "DevOps",
    "Chatbot", "API", "REST", "Excel", "Automation",
    "Testing", "Unit Test", "API Testing",
    ## Expansión desde el CV
    "OpenLayers", "Chart.js", "Leaflet.js", "Vite", "PWA",
    "Service Workers", "IndexedDB", "NASA FIRMS", "Open-Meteo",
    "MCP", "Vercel AI", "Zavu API", "Faces.app AI",
    "RAG", "Gemini API", "Ollama", "GHG Protocol",
    "pandas", "scipy", "spm1d", "plotly", "matplotlib",
    "Tkinter", "PyInstaller", "LaTeX", "PL/pgSQL",
    "Google Cloud Translate", "Mobility", "i18n",
    "FOCUS FinOps", "SPSS", "PySpark", "Airflow",
    "MVP", "DDD", "POO", "SOLID",
    "SCRUM", "Kanban", "Agile", "GitOps",
    "CDN", "ORM", "API REST", "OAuth", "JWT",
    "npm", "yarn", "webpack", "Babel", "ESLint",
    "Figma", "Adobe XD", "Photoshop", "Illustrator",
    "Notion", "Confluence", "Slack", "Discord",
    "Stripe", "PayPal", "Mercado Pago",
    "iOS", "Android", "React Native", "Flutter",
    "WebSockets", "SSE", "gRPC",
    "Deep Learning", "NLP", "Computer Vision", "TensorFlow", "PyTorch",
    "Scikit-learn", "XGBoost", "LightGBM",
    "Tableau", "Power BI", "Looker",
    "SAP", "Salesforce", "HubSpot",
    "Google Analytics", "Google Tag Manager", "SEO", "SEM",
    "C", "C++", "C#", ".NET", "Go", "Rust", "PHP", "Scala", "Kotlin", "Swift",
    "R", "MATLAB", "Julia",
    "Hadoop", "Spark", "Kafka", "Flink",
    "Snowflake", "BigQuery", "Redshift",
    "CloudFormation", "CDK", "Pulumi",
    "Vagrant", "VirtualBox", "VMware",
}

CORE_SKILLS_LOWER = {s.lower(): s for s in CORE_SKILLS}

TECH_KEYWORDS = {
    "js", "ts", "py", "rb", "go", "rs", "vue",
    "api", "sdk", "cli", "ui", "ux", "db", "sql",
    "npm", "yarn", "pip", "gem", "cargo",
}

def _strip_version(name: str) -> str:
    name = re.sub(r'[ \t]*\d+\.\d+.*$', '', name)
    name = re.sub(r'[ \t]*\d+.*$', '', name)
    name = re.sub(r'\s*\([^)]*\)', '', name)
    name = re.sub(r'\s*\+\s*$', '', name)
    return name.strip()

def _looks_like_tech(term: str) -> bool:
    if not term or len(term) <= 1:
        return False
    if re.match(r'^[A-Z][a-z]', term):
        return True
    if re.match(r'^[A-Z]{2,}', term):
        return True
    if '.' in term and not term.endswith('.'):
        return True
    if term.lower() in TECH_KEYWORDS:
        return True
    return False

def _extract_skills(text: str) -> list[str]:
    skills = set()
    patterns = [
        r"_Stack(?: especializado)?_: (.+)",
        r"Stack: (.+)",
        r"\*Stack\*: (.+)",
        r"\*Herramientas\*: (.+)",
    ]
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            parts = re.split(r"[,;·|•]", m.group(1))
            for part in parts:
                part = part.strip().rstrip(".")
                part = _strip_version(part)
                if part and len(part) > 1:
                    if part in CORE_SKILLS:
                        skills.add(part)
                        continue
                    term_lower = part.lower()
                    matched = False
                    for core_lower, core_orig in CORE_SKILLS_LOWER.items():
                        if core_lower in term_lower or term_lower in core_lower:
                            skills.add(core_orig)
                            matched = True
                            break
                    if not matched and _looks_like_tech(part):
                        skills.add(part)

    if not skills:
        return ["Python", "Ruby on Rails", "JavaScript", "SQL", "Selenium"]
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
                    "Playwright", "CI/CD", "TypeScript", "Java", "React"],
            experience_years=1.5,
            education="Ingeniero Civil Informático — PUCV (2025)",
            projects=["KineViz", "FireGuard", "MCP Server"],
            preferred_roles=["QA Automation", "Full Stack", "Backend"],
            locations=["Valparaíso", "Santiago", "Remoto Chile", "Remoto Mundial"],
            languages=["Spanish", "English C2"],
        )

    cv_path = cv_rel_path or os.path.join(repo_path, "cv", "cv-es.adoc")
    resume_path = os.path.join(repo_path, "resume", "resume-es.adoc")

    # Read both for structured field parsing (skills, title, projects, etc.)
    text = ""
    for p in [cv_path, resume_path]:
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                text += f.read() + "\n"

    # For LLM context, use only the resume — concise, complete, curated
    raw_text = ""
    if os.path.isfile(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

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
        raw_text=raw_text,
    )
