#!/usr/bin/env python3
"""
Google Dork Scanner - Ferramenta de auditoria de segurança
===========================================================
Gera consultas de reconhecimento (Google Dorks) para um domínio e,
opcionalmente, executa-as automaticamente via API do Serper.dev.

Dois modos:
  1. MANUAL  - Gera links de busca (terminal + arquivo HTML clicável).
  2. API     - Busca automática via Serper.dev com dashboard e relatórios.

Uso apenas em sistemas que você possui ou tem autorização explícita
para testar.

Autor: Security Tools
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from html import escape
from http.client import HTTPSConnection
from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# Interface: usa "rich" quando disponível, com fallback para texto simples.
# ---------------------------------------------------------------------------
try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    RICH = True
    console = Console()
except ImportError:  # pragma: no cover - caminho de fallback
    RICH = False
    console = None


VERSION = "3.1"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".dork_scanner_config.json")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dorks_database.json")

SERPER_HOST = "google.serper.dev"
DEFAULT_GL = "br"
DEFAULT_HL = "pt"

SEVERITY_ORDER = {"critico": 0, "alto": 1, "medio": 2, "baixo": 3}
SEVERITY_STYLE = {
    "critico": "bold white on red",
    "alto": "bold red",
    "medio": "yellow",
    "baixo": "cyan",
}
SEVERITY_LABEL = {
    "critico": "CRÍTICO",
    "alto": "ALTO",
    "medio": "MÉDIO",
    "baixo": "BAIXO",
}


# ---------------------------------------------------------------------------
# Modelo de dados
# ---------------------------------------------------------------------------
class SearchStatus(Enum):
    """Resultado de uma busca via API — separa 'vazio' de 'erro'."""
    FOUND = "encontrado"      # busca ok, com resultados
    EMPTY = "vazio"           # busca ok, sem resultados
    ERROR = "erro"            # falha (rede, JSON, HTTP inesperado)
    QUOTA = "cota"            # limite/autorização da API esgotada (401/403/429)


@dataclass
class Category:
    key: str
    description: str
    severity: str
    dorks: list[str]


@dataclass
class DorkResult:
    category: str
    severity: str
    dork: str
    status: SearchStatus
    urls: list[dict] = field(default_factory=list)
    error: str = ""


# ---------------------------------------------------------------------------
# Helpers de saída (funcionam com ou sem rich)
# ---------------------------------------------------------------------------
def out(msg: str = "") -> None:
    if RICH:
        console.print(msg)
    else:
        # remove marcações rich simples do fallback
        print(re.sub(r"\[/?[^\]]+\]", "", msg))


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def banner() -> None:
    if RICH:
        console.print(
            Panel(
                Text.assemble(
                    ("🔍  GOOGLE DORK SCANNER  🔍\n", "bold cyan"),
                    (f"Ferramenta de Auditoria de Segurança  ·  v{VERSION}", "dim"),
                ),
                box=box.DOUBLE,
                border_style="cyan",
                padding=(1, 4),
            )
        )
    else:
        print("=" * 60)
        print(f"  GOOGLE DORK SCANNER v{VERSION}")
        print("  Ferramenta de Auditoria de Segurança")
        print("=" * 60)


def mask_key(key: str) -> str:
    """Mostra apenas os últimos 4 caracteres da API key."""
    if not key:
        return ""
    return f"{'•' * 8}{key[-4:]}" if len(key) > 4 else "•" * len(key)


# ---------------------------------------------------------------------------
# Configuração / API key
# ---------------------------------------------------------------------------
def load_saved_key() -> str | None:
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f).get("api_key")
    except (json.JSONDecodeError, OSError) as exc:
        out(f"[yellow]⚠ Não foi possível ler a config: {exc}[/yellow]")
        return None


def save_key(key: str) -> bool:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_key": key}, f)
        os.chmod(CONFIG_FILE, 0o600)
        return True
    except OSError as exc:
        out(f"[yellow]⚠ Não foi possível salvar a config: {exc}[/yellow]")
        return False


def resolve_api_key(cli_key: str | None, interactive: bool) -> str | None:
    """Precedência: argumento CLI > env SERPER_API_KEY > config salva > pergunta."""
    if cli_key:
        return cli_key
    env_key = os.environ.get("SERPER_API_KEY")
    if env_key:
        return env_key
    saved = load_saved_key()
    if saved and interactive:
        out(f"[green]✓ API Key salva encontrada:[/green] {mask_key(saved)}")
        if not RICH or Confirm.ask("Usar esta API Key?", default=True):
            return saved
    elif saved:
        return saved

    if not interactive:
        return None

    out()
    out("[cyan]Obtenha uma API Key gratuita em https://serper.dev "
        "(2.500 buscas/mês).[/cyan]")
    key = (Prompt.ask("Cole sua API Key") if RICH
           else input("Cole sua API Key: ")).strip()
    if len(key) < 20:
        out("[red]API Key inválida.[/red]")
        return None
    if (RICH and Confirm.ask("Salvar para as próximas execuções?", default=True)) \
            or (not RICH and input("Salvar? (s/n): ").strip().lower() == "s"):
        save_key(key)
    return key


# ---------------------------------------------------------------------------
# Domínio
# ---------------------------------------------------------------------------
DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.[A-Za-z0-9-]{1,63})+$"
)


def normalize_domain(raw: str) -> str | None:
    raw = raw.strip()
    raw = re.sub(r"^https?://", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"^www\.", "", raw, flags=re.IGNORECASE)
    raw = raw.split("/")[0].strip()
    return raw if DOMAIN_RE.match(raw) else None


def ask_domain() -> str:
    out("[red]⚠️  AVISO LEGAL:[/red] use apenas em sistemas que você "
        "possui ou tem autorização explícita para testar.")
    while True:
        raw = (Prompt.ask("Digite o domínio (ex: exemplo.com)") if RICH
               else input("Domínio (ex: exemplo.com): "))
        domain = normalize_domain(raw)
        if domain:
            return domain
        out("[red]Domínio inválido. Tente novamente.[/red]")


# ---------------------------------------------------------------------------
# Carregamento de dorks
# ---------------------------------------------------------------------------
def load_categories(domain: str) -> list[Category]:
    if not os.path.exists(DB_FILE):
        out(f"[red]Base de dorks não encontrada em {DB_FILE}[/red]")
        sys.exit(1)
    try:
        with open(DB_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        out(f"[red]Erro ao ler {DB_FILE}: {exc}[/red]")
        sys.exit(1)

    categories: list[Category] = []
    for key, info in data.get("dork_categories", {}).items():
        dorks = [d.replace("{domain}", domain) for d in info.get("dorks", [])]
        categories.append(
            Category(
                key=key,
                description=info.get("description", key),
                severity=info.get("severity", "medio"),
                dorks=dorks,
            )
        )
    # incluir dorks personalizados, se houver
    custom = data.get("custom_dorks", {})
    examples = [d for d in custom.get("examples", []) if "YOUR_CUSTOM_DORK" not in d]
    if examples:
        categories.append(
            Category("custom", "Dorks personalizados", "medio",
                     [d.replace("{domain}", domain) for d in examples])
        )
    categories.sort(key=lambda c: SEVERITY_ORDER.get(c.severity, 9))
    return categories


def choose_categories(categories: list[Category]) -> list[Category]:
    if not RICH:
        return categories  # sem rich, roda tudo
    table = Table(box=box.SIMPLE, show_edge=False)
    table.add_column("#", justify="right", style="bold")
    table.add_column("Categoria")
    table.add_column("Severidade")
    table.add_column("Dorks", justify="right")
    for i, c in enumerate(categories, 1):
        table.add_row(
            str(i),
            c.description,
            f"[{SEVERITY_STYLE[c.severity]}] {SEVERITY_LABEL[c.severity]} [/]",
            str(len(c.dorks)),
        )
    console.print(table)
    out("[dim]ENTER = todas · ou informe números separados por vírgula "
        "(ex: 1,3,5)[/dim]")
    raw = Prompt.ask("Categorias", default="").strip()
    if not raw:
        return categories
    chosen = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(categories):
            chosen.append(categories[int(part) - 1])
    return chosen or categories


# ---------------------------------------------------------------------------
# Serper.dev
# ---------------------------------------------------------------------------
def search_serper(dork: str, api_key: str, gl: str, hl: str) -> DorkResult:
    payload = json.dumps({"q": dork, "num": 10, "gl": gl, "hl": hl})
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    conn = None
    try:
        conn = HTTPSConnection(SERPER_HOST, timeout=20)
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        body = res.read().decode("utf-8", errors="replace")
        if res.status in (401, 403, 429):
            return DorkResult("", "", dork, SearchStatus.QUOTA,
                              error=f"HTTP {res.status}: {body[:120]}")
        if res.status != 200:
            return DorkResult("", "", dork, SearchStatus.ERROR,
                              error=f"HTTP {res.status}: {body[:120]}")
        data = json.loads(body)
        urls = [
            {"title": it.get("title", ""), "link": it.get("link", ""),
             "snippet": it.get("snippet", "")}
            for it in data.get("organic", [])
        ]
        return DorkResult("", "", dork,
                          SearchStatus.FOUND if urls else SearchStatus.EMPTY,
                          urls=urls)
    except (OSError, json.JSONDecodeError) as exc:
        return DorkResult("", "", dork, SearchStatus.ERROR, error=str(exc))
    finally:
        if conn is not None:
            conn.close()


# ---------------------------------------------------------------------------
# Modo manual (links)
# ---------------------------------------------------------------------------
def google_url(dork: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(dork)}"


def run_manual(categories: list[Category], domain: str,
               open_html: bool) -> None:
    total = sum(len(c.dorks) for c in categories)
    out(f"[green]✓ Domínio:[/green] {domain}   "
        f"[green]✓ Total de dorks:[/green] {total}\n")
    n = 0
    for c in categories:
        out(f"[{SEVERITY_STYLE[c.severity]}] {SEVERITY_LABEL[c.severity]} [/] "
            f"[bold]{c.description}[/bold] ({len(c.dorks)})")
        for dork in c.dorks:
            n += 1
            url = google_url(dork)
            if RICH:
                console.print(f"  [cyan]{n:>3}[/cyan]  {dork}")
                console.print(f"       [link={url}][blue underline]{url}"
                              f"[/blue underline][/link]")
            else:
                print(f"  {n:>3}  {dork}\n       {url}")
        out()
    html_path = write_html_links(categories, domain)
    out(f"[green]✓ {total} links gerados.[/green]  "
        f"HTML clicável: [cyan]{html_path}[/cyan]")
    if open_html:
        webbrowser.open(f"file://{os.path.abspath(html_path)}")


def write_html_links(categories: list[Category], domain: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"dorks_{domain}_{ts}.html"
    rows = []
    for c in categories:
        rows.append(f'<h2>{escape(c.description)} '
                    f'<span class="sev {c.severity}">'
                    f'{SEVERITY_LABEL[c.severity]}</span></h2><ul>')
        for dork in c.dorks:
            url = google_url(dork)
            rows.append(f'<li><a href="{escape(url)}" target="_blank">'
                        f'{escape(dork)}</a></li>')
        rows.append("</ul>")
    html = f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<title>Dorks · {escape(domain)}</title><style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;
padding:0 1rem;background:#0d1117;color:#e6edf3}}
h1{{color:#58a6ff}}h2{{margin-top:1.5rem;border-bottom:1px solid #30363d;
padding-bottom:.3rem}}a{{color:#79c0ff;text-decoration:none}}
a:hover{{text-decoration:underline}}li{{margin:.25rem 0}}
.sev{{font-size:.7rem;padding:.1rem .4rem;border-radius:4px;color:#fff}}
.critico{{background:#da3633}}.alto{{background:#e16f24}}
.medio{{background:#9e6a03}}.baixo{{background:#1f6feb}}
</style></head><body><h1>🔍 Google Dorks — {escape(domain)}</h1>
<p>Gerado em {datetime.now():%Y-%m-%d %H:%M}. Uso autorizado apenas.</p>
{''.join(rows)}</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


# ---------------------------------------------------------------------------
# Modo API
# ---------------------------------------------------------------------------
def run_api(categories: list[Category], domain: str, api_key: str,
            gl: str, hl: str, workers: int) -> list[DorkResult]:
    jobs = [(c, dork) for c in categories for dork in c.dorks]
    total = len(jobs)
    results: list[DorkResult] = []
    quota_hit = False

    def do(job):
        c, dork = job
        r = search_serper(dork, api_key, gl, hl)
        r.category, r.severity = c.description, c.severity
        return r

    if RICH:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        )
        ctx = progress
    else:
        progress = None
        ctx = _NullCtx()

    with ctx:
        task = progress.add_task("Escaneando", total=total) if RICH else None
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(do, j): j for j in jobs}
            done = 0
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                done += 1
                if RICH:
                    progress.update(task, advance=1,
                                    description=f"Escaneando  ({done}/{total})")
                else:
                    print(f"[{done}/{total}] {r.dork[:60]}  "
                          f"-> {r.status.value}")
                if r.status is SearchStatus.QUOTA and not quota_hit:
                    quota_hit = True
                    for f in futures:
                        f.cancel()
                    out(f"\n[red]⚠ Cota/autorização da API esgotada: "
                        f"{r.error}[/red]")
                    out("[red]Scan interrompido. Verifique sua API Key/limite."
                        "[/red]")
                    break
    return results


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False


# ---------------------------------------------------------------------------
# Dashboard e relatórios
# ---------------------------------------------------------------------------
def summarize(results: list[DorkResult]) -> dict:
    return {
        "total": len(results),
        "found": sum(r.status is SearchStatus.FOUND for r in results),
        "empty": sum(r.status is SearchStatus.EMPTY for r in results),
        "error": sum(r.status is SearchStatus.ERROR for r in results),
        "quota": sum(r.status is SearchStatus.QUOTA for r in results),
    }


def dashboard(results: list[DorkResult], domain: str) -> None:
    s = summarize(results)
    scanned = s["found"] + s["empty"]
    rate = (s["found"] / scanned * 100) if scanned else 0

    if RICH:
        table = Table(title=f"📊 Dashboard — {domain}", box=box.ROUNDED,
                      title_style="bold cyan")
        table.add_column("Métrica")
        table.add_column("Valor", justify="right")
        table.add_row("Total de dorks", str(s["total"]))
        table.add_row("[green]Com resultados[/green]", f"[green]{s['found']}[/green]")
        table.add_row("Sem resultados", str(s["empty"]))
        if s["error"]:
            table.add_row("[red]Erros[/red]", f"[red]{s['error']}[/red]")
        if s["quota"]:
            table.add_row("[red]Bloqueios de cota[/red]", f"[red]{s['quota']}[/red]")
        table.add_row("Taxa de descoberta", f"{rate:.1f}%")
        console.print(table)
    else:
        print(f"Total {s['total']} | com resultados {s['found']} | "
              f"sem {s['empty']} | erros {s['error']} | cota {s['quota']}")

    found = [r for r in results if r.status is SearchStatus.FOUND]
    if not found:
        out("[green]Nenhuma exposição encontrada nas dorks executadas.[/green]")
        if s["error"] or s["quota"]:
            out("[yellow]⚠ Atenção: houve erros/bloqueios — o resultado pode "
                "estar incompleto.[/yellow]")
        return

    found.sort(key=lambda r: SEVERITY_ORDER.get(r.severity, 9))
    if RICH:
        t = Table(title="🔎 Exposições encontradas (por severidade)",
                  box=box.SIMPLE, title_style="bold red")
        t.add_column("Sev.")
        t.add_column("Categoria")
        t.add_column("Dork")
        t.add_column("URLs", justify="right")
        for r in found:
            t.add_row(f"[{SEVERITY_STYLE[r.severity]}]"
                      f"{SEVERITY_LABEL[r.severity]}[/]",
                      r.category, r.dork, str(len(r.urls)))
        console.print(t)
    else:
        for r in found:
            print(f"  [{SEVERITY_LABEL[r.severity]}] {r.dork} "
                  f"({len(r.urls)} URLs)")


def save_report(results: list[DorkResult], domain: str, fmt: str,
                path: str | None) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = path or f"scan_{domain}_{ts}.{fmt}"
    found = [r for r in results if r.status is SearchStatus.FOUND]
    found.sort(key=lambda r: SEVERITY_ORDER.get(r.severity, 9))
    s = summarize(results)

    if fmt == "json":
        payload = {
            "domain": domain,
            "generated_at": datetime.now().isoformat(),
            "summary": s,
            "findings": [
                {"severity": r.severity, "category": r.category,
                 "dork": r.dork, "urls": r.urls} for r in found
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    elif fmt == "csv":
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["severidade", "categoria", "dork", "url", "titulo"])
            for r in found:
                for u in r.urls:
                    w.writerow([r.severity, r.category, r.dork,
                                u["link"], u["title"]])
    elif fmt == "html":
        rows = []
        for r in found:
            links = "".join(
                f'<li><a href="{escape(u["link"])}" target="_blank">'
                f'{escape(u["link"])}</a></li>' for u in r.urls)
            rows.append(f'<div class="finding {r.severity}"><h3>'
                        f'<span class="sev">{SEVERITY_LABEL[r.severity]}</span> '
                        f'{escape(r.dork)}</h3><small>{escape(r.category)}</small>'
                        f'<ul>{links}</ul></div>')
        html = f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<title>Relatório · {escape(domain)}</title><style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;
padding:0 1rem;background:#0d1117;color:#e6edf3}}h1{{color:#58a6ff}}
a{{color:#79c0ff}}.finding{{border-left:4px solid #30363d;padding:.5rem 1rem;
margin:1rem 0;background:#161b22;border-radius:6px}}
.critico{{border-color:#da3633}}.alto{{border-color:#e16f24}}
.medio{{border-color:#9e6a03}}.baixo{{border-color:#1f6feb}}
.sev{{font-size:.7rem;padding:.1rem .4rem;border-radius:4px;background:#30363d}}
</style></head><body><h1>🔍 Relatório — {escape(domain)}</h1>
<p>{datetime.now():%Y-%m-%d %H:%M} · {s['found']} exposições · uso autorizado.</p>
{''.join(rows) or '<p>Nenhuma exposição encontrada.</p>'}</body></html>"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
    else:  # txt
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"GOOGLE DORK SCAN REPORT\nDomínio: {domain}\n"
                    f"Data: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"Total: {s['total']} | Com resultados: {s['found']} | "
                    f"Sem: {s['empty']} | Erros: {s['error']} | "
                    f"Cota: {s['quota']}\n" + "=" * 70 + "\n\n")
            for r in found:
                f.write(f"[{SEVERITY_LABEL[r.severity]}] {r.category}\n"
                        f"  {r.dork}  ({len(r.urls)} URLs)\n")
                for u in r.urls:
                    f.write(f"    - {u['link']}\n")
                f.write("\n")
    return path


# ---------------------------------------------------------------------------
# Fluxo interativo
# ---------------------------------------------------------------------------
def interactive() -> None:
    while True:
        clear_screen()
        banner()
        if RICH:
            menu = Table(box=box.SIMPLE, show_header=False)
            menu.add_column(style="bold")
            menu.add_row("[green][1][/green] 🔗 Modo Manual (links + HTML clicável)")
            menu.add_row("[cyan][2][/cyan] 🚀 Modo Serper.dev API (busca automática)")
            menu.add_row("[red][0][/red] ❌ Sair")
            console.print(menu)
            choice = Prompt.ask("Escolha", choices=["0", "1", "2"], default="1")
        else:
            print("[1] Modo Manual\n[2] Modo API\n[0] Sair")
            choice = input("Escolha [0-2]: ").strip()

        if choice == "0":
            out("[cyan]Encerrando...[/cyan]")
            return
        if choice not in ("1", "2"):
            continue

        api_key = None
        if choice == "2":
            api_key = resolve_api_key(None, interactive=True)
            if not api_key:
                out("[red]Sem API Key válida. Voltando ao menu.[/red]")
                _pause()
                continue

        domain = ask_domain()
        categories = load_categories(domain)
        categories = choose_categories(categories)

        if choice == "1":
            open_html = (Confirm.ask("Abrir o HTML no navegador agora?",
                                     default=False) if RICH else False)
            run_manual(categories, domain, open_html)
        else:
            results = run_api(categories, domain, api_key,
                              DEFAULT_GL, DEFAULT_HL, workers=5)
            dashboard(results, domain)
            if any(r.status is SearchStatus.FOUND for r in results):
                if not RICH or Confirm.ask("Salvar relatório?", default=True):
                    fmt = (Prompt.ask("Formato", choices=["html", "json", "csv", "txt"],
                                      default="html") if RICH else "html")
                    p = save_report(results, domain, fmt, None)
                    out(f"[green]✓ Relatório salvo em[/green] [cyan]{p}[/cyan]")
        _pause()


def _pause() -> None:
    if RICH:
        console.input("\n[dim]Pressione ENTER para continuar...[/dim]")
    else:
        input("\nPressione ENTER para continuar...")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Google Dork Scanner — auditoria de segurança "
                    "(uso autorizado apenas).",
        epilog="Sem argumentos, abre o menu interativo.",
    )
    p.add_argument("-d", "--domain", help="domínio alvo (ex: exemplo.com)")
    p.add_argument("--api", action="store_true",
                   help="usa a API Serper.dev (busca automática)")
    p.add_argument("--api-key", help="API key do Serper.dev "
                   "(ou use a env SERPER_API_KEY)")
    p.add_argument("-o", "--output", help="arquivo de saída do relatório")
    p.add_argument("-f", "--format", choices=["html", "json", "csv", "txt"],
                   default="html", help="formato do relatório (padrão: html)")
    p.add_argument("--gl", default=DEFAULT_GL, help="país da busca (padrão: br)")
    p.add_argument("--hl", default=DEFAULT_HL, help="idioma da busca (padrão: pt)")
    p.add_argument("-w", "--workers", type=int, default=5,
                   help="buscas paralelas no modo API (padrão: 5)")
    p.add_argument("--open", action="store_true",
                   help="abre o HTML gerado no navegador (modo manual)")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p


def run_cli(args: argparse.Namespace) -> int:
    domain = normalize_domain(args.domain)
    if not domain:
        out(f"[red]Domínio inválido: {args.domain}[/red]")
        return 2
    categories = load_categories(domain)

    if args.api:
        api_key = resolve_api_key(args.api_key, interactive=False)
        if not api_key:
            out("[red]API Key ausente. Use --api-key ou a env "
                "SERPER_API_KEY.[/red]")
            return 2
        results = run_api(categories, domain, api_key,
                          args.gl, args.hl, args.workers)
        dashboard(results, domain)
        if any(r.status is SearchStatus.FOUND for r in results):
            path = save_report(results, domain, args.format, args.output)
            out(f"[green]✓ Relatório salvo em[/green] [cyan]{path}[/cyan]")
        if any(r.status is SearchStatus.QUOTA for r in results):
            return 1
    else:
        run_manual(categories, domain, args.open)
    return 0


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.domain:
            sys.exit(run_cli(args))
        interactive()
    except KeyboardInterrupt:
        out("\n[yellow]Operação cancelada pelo usuário.[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
