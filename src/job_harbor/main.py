"""Job Harbor CLI — main entrypoint."""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from .model import Profile, Job
from .profile import load_profile
from .scrapers import RemoteOKScraper, HimalayasScraper, RemotiveScraper, GetOnBoardScraper, VacantesDigitalesScraper, JoobleScraper
from .matcher import KeywordMatcher, LLMMatcher
from . import db

console = Console()

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.yaml"
DOTENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def _load_dotenv():
    if DOTENV_PATH.exists():
        with open(DOTENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


def _load_config() -> dict:
    defaults = {
        "preferences": {
            "locations": ["Valparaíso", "Santiago", "Remoto Chile", "Remoto Mundial"],
            "min_match_score": 40,
            "keywords": ["QA", "Automation", "Full Stack", "Backend", "Python", "Rails"],
        }
    }
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return {**defaults, **yaml.safe_load(f)}
    return defaults


def _save_default_config():
    defaults = {
        "preferences": {
            "locations": ["Valparaíso", "Santiago", "Remoto Chile", "Remoto Mundial"],
            "min_match_score": 40,
            "keywords": ["QA", "Automation", "Full Stack", "Backend", "Python", "Rails"],
        }
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(defaults, f, allow_unicode=True, sort_keys=False)
    console.print(f"[dim]Config created at {CONFIG_PATH}[/dim]")


def cmd_run(llm: Optional[str] = None):
    _load_dotenv()
    if not CONFIG_PATH.exists():
        _save_default_config()

    config = _load_config()
    db.init_db()

    with console.status("[bold cyan]Loading profile...") as status:
        profile = load_profile()
        console.print(f"  Profile: [green]{profile.name}[/green]")
        console.print(f"  Skills: {', '.join(profile.skills[:8])}...")

    status.update("[bold cyan]Scraping jobs...")
    scrapers = [
        RemoteOKScraper(),
        HimalayasScraper(),
        RemotiveScraper(),
        GetOnBoardScraper(),
        VacantesDigitalesScraper(),
        JoobleScraper(),
    ]

    all_jobs = []
    for scraper in scrapers:
        try:
            status.update(f"[bold cyan]Scraping {scraper.name}...")
            jobs = scraper.scrape(limit=20)
            all_jobs.extend(jobs)
            console.print(f"  [green]OK[/green] {scraper.name}: {len(jobs)} ofertas")
        except Exception as e:
            console.print(f"  [red]ERR[/red] {scraper.name}: {e}")

    console.print(f"\n[yellow]Total: {len(all_jobs)} ofertas encontradas[/yellow]")

    status.update("[bold cyan]Matching with keywords...")
    kw_matcher = KeywordMatcher(profile)

    new_jobs = 0
    for job in all_jobs:
        if db.save_job(job):
            new_jobs += 1
        score, reason, skills_found, skills_missing = kw_matcher.match(job)
        job.match_score = score
        job.match_reason = reason
        job.skill_matches = skills_found
        job.skill_gaps = skills_missing
        db.update_job_score(job.url, score, reason)

    if llm:
        status.update("[bold cyan]Running LLM matcher...")
        try:
            llm_matcher = LLMMatcher(profile, backend=llm)
            matched = db.get_matched_jobs(min_score=30)
            for row in matched[:10]:
                job = Job(
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    url=row["url"],
                    description=row["description"] or "",
                )
                score, reason, sf, sg = llm_matcher.match(job)
                db.update_job_score(row["url"], score, reason)
        except Exception as e:
            console.print(f"  [red]LLM matcher error: {e}[/red]")

    db.log_run(len(all_jobs), new_jobs, llm_used=bool(llm))

    matched = db.get_matched_jobs(min_score=config["preferences"]["min_match_score"])

    console.print(f"\n[bold]Job Harbor — {len(all_jobs)} ofertas analizadas | {len(matched)} relevantes[/bold]\n")

    if matched:
        table = Table(box=None)
        table.add_column("", width=4)
        table.add_column("Oferta", width=40)
        table.add_column("Score", justify="right", width=6)
        table.add_column("Empresa", width=20)
        table.add_column("Ubicación", width=18)

        for i, job in enumerate(matched):
            score_color = "green" if job["match_score"] >= 70 else "yellow" if job["match_score"] >= 50 else "red"
            emoji = "#1" if i == 0 else "#2" if i == 1 else "#3" if i == 2 else "  "
            table.add_row(
                emoji,
                job["title"][:38],
                f"[{score_color}]{job['match_score']:.0f}%[/{score_color}]",
                job["company"][:18],
                job["location"][:16],
            )

        console.print(table)

        for i, job in enumerate(matched[:5]):
            console.print(f"\n[bold]{'#1' if i==0 else '#2' if i==1 else '#3' if i==2 else '  '} "
                         f"{job['title']}[/bold] - [cyan]{job['company']}[/cyan]")
            console.print(f"   [link={job['url']}]{job['url']}[/link]")
            if job["match_reason"]:
                console.print(f"   [dim]{job['match_reason']}[/dim]")
    else:
        console.print("[yellow]No se encontraron ofertas con match suficiente.[/yellow]")
        console.print("[dim]Prueba reducir min_match_score en config.yaml[/dim]")


def cmd_list():
    db.init_db()
    jobs = db.get_all_jobs()

    if not jobs:
        console.print("[yellow]No hay ofertas almacenadas. Corre 'job-harbor run' primero.[/yellow]")
        return

    table = Table(box=None)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Título", width=40)
    table.add_column("Empresa", width=20)
    table.add_column("Fuente", width=12)
    table.add_column("Fecha", width=12)

    for j in jobs[:30]:
        score_color = "green" if j["match_score"] >= 70 else "yellow" if j["match_score"] >= 50 else "red"
        table.add_row(
            f"[{score_color}]{j['match_score']:.0f}%[/{score_color}]",
            j["title"][:38],
            j["company"][:18],
            j["source"],
            j["updated_at"][:10] if j["updated_at"] else "",
        )

    console.print(table)
    console.print(f"\n[dim]Mostrando {min(len(jobs), 30)} de {len(jobs)} ofertas[/dim]")


def cmd_history():
    db.init_db()
    runs = db.get_history()

    if not runs:
        console.print("[yellow]No hay historial de ejecuciones.[/yellow]")
        return

    table = Table(title="Historial de ejecuciones", box=None)
    table.add_column("Fecha", width=20)
    table.add_column("Ofertas", justify="right", width=8)
    table.add_column("Match", justify="right", width=8)
    table.add_column("LLM", width=6)

    for r in runs:
        table.add_row(
            r["timestamp"][:19],
            str(r["total_jobs"]),
            str(r["matched_jobs"]),
            "yes" if r["llm_used"] else "no",
        )

    console.print(table)


def cli():
    parser = argparse.ArgumentParser(
        description="Job Harbor — Encuentra las mejores ofertas para tu perfil"
    )
    sub = parser.add_subparsers(dest="command", help="Comandos")

    run_parser = sub.add_parser("run", help="Ejecutar búsqueda y matching")
    run_parser.add_argument("--llm", nargs="?", const="gemini", choices=["gemini", "ollama"],
                           help="Usar LLM para matching semántico")

    sub.add_parser("list", help="Listar ofertas almacenadas")
    sub.add_parser("history", help="Ver historial de ejecuciones")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(llm=args.llm)
    elif args.command == "list":
        cmd_list()
    elif args.command == "history":
        cmd_history()
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
