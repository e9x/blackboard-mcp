#!/usr/bin/env python3
"""
setup.py — One-time setup wizard for Blackboard MCP

Works with ANY university that uses Blackboard Learn (Ultra or Classic).

Run this once:
    python3 setup.py

What it does:
  1. Asks for your university's Blackboard URL
  2. Auto-detects Blackboard Ultra vs Classic interface
  3. Opens a real browser — you log in as normal (works with any SSO / MFA)
  4. Tests the connection and lists your courses
  5. Optionally saves credentials to the OS keychain for silent auto-relogin
  6. Auto-configures all detected AI coding assistants
"""
from __future__ import annotations

import asyncio
import getpass
import json
import os
import re
import sys
from pathlib import Path

# ── Auto-bootstrap: create .venv and re-exec inside it if needed ─────────────
# Only runs when setup.py is executed as a script. When imported as a module
# (e.g. by tests or CI), the bootstrap is skipped entirely.
if __name__ == "__main__" and os.environ.get("_BB_MCP_VENV") != "1":
    _HERE = Path(__file__).parent.resolve()
    _VENV = _HERE / ".venv"
    _VENV_PY = _VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python3")
    import subprocess as _sp
    if not _VENV_PY.exists():
        print("Setting up environment (one-time, ~1 minute)...", flush=True)
        _sp.check_call([sys.executable, "-m", "venv", str(_VENV)])
        _sp.check_call([str(_VENV_PY), "-m", "pip", "install", "-q", "-r",
                        str(_HERE / "requirements.txt")])
        print("Downloading browser for login (one-time, ~150MB)...", flush=True)
        _sp.check_call([str(_VENV_PY), "-m", "playwright", "install", "chromium"])
    env = os.environ.copy()
    env["_BB_MCP_VENV"] = "1"
    sys.exit(_sp.call([str(_VENV_PY)] + sys.argv, env=env))
# ─────────────────────────────────────────────────────────────────────────────

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule

console = Console()

PROJECT_DIR = Path(__file__).parent
PYTHON = sys.executable
ENV_FILE = PROJECT_DIR / ".env"

# ── Known university Blackboard URLs (for reference hints only) ───────────────
KNOWN_UNIVERSITIES: dict[str, str] = {
    "cdu":        "https://online.cdu.edu.au",
    "latrobe":    "https://latrobe.blackboard.com",
    "federation": "https://federation.edu.au/blackboard",
    "uwa":        "https://lms.uwa.edu.au",
}

# ─────────────────────────────────────────────────────────────────────────────


def banner() -> None:
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Blackboard MCP — Setup Wizard[/bold cyan]\n"
        "[dim]Connect any AI assistant to your university Blackboard account[/dim]",
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()


def step(n: int, total: int, title: str) -> None:
    console.print(Rule(f"[bold]Step {n}/{total}[/bold]  {title}", style="cyan"))
    console.print()


def success(msg: str) -> None:
    console.print(f"  [bold green]✅[/bold green] {msg}")


def info(msg: str) -> None:
    console.print(f"  [dim]ℹ[/dim]  {msg}")


def warn(msg: str) -> None:
    console.print(f"  [yellow]⚠[/yellow]  {msg}")


def error_msg(msg: str) -> None:
    console.print(f"  [bold red]✗[/bold red]  {msg}")


# ─────────────────────────────────────────────────────────────────────────────
#  TTY-safe input — handles piped install (curl | bash) and other non-TTY runs
# ─────────────────────────────────────────────────────────────────────────────

# Populated from CLI args at startup. When set, prompts use these instead of
# blocking on stdin — makes setup.py fully scriptable.
_CLI_ARGS: dict = {"url": None, "yes": False, "no_keychain": False}


def _stdin_is_tty() -> bool:
    """True if stdin is a real terminal (not a pipe / heredoc / null)."""
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except Exception:
        return False


def safe_prompt(question: str, default: str | None = None) -> str:
    """Prompt the user, returning `default` if stdin is closed or not a TTY."""
    if not _stdin_is_tty():
        if default is None:
            error_msg(
                "This wizard needs a real terminal but stdin is a pipe.\n"
                "  • If you ran `curl ... | bash`, re-run with: "
                "`bash <(curl -fsSL <url>)` so prompts work,\n"
                "  • Or pass values non-interactively: "
                "`python3 setup.py --url https://your.uni.edu --yes`"
            )
            sys.exit(2)
        return default
    try:
        return Prompt.ask(question, default=default) if default is not None \
            else Prompt.ask(question)
    except (EOFError, KeyboardInterrupt):
        if default is not None:
            return default
        error_msg("Input closed unexpectedly. Aborting.")
        sys.exit(2)


def safe_confirm(question: str, default: bool = False) -> bool:
    """Confirm prompt with a TTY-safe default fallback."""
    if not _stdin_is_tty():
        return default
    try:
        return Confirm.ask(question, default=default)
    except (EOFError, KeyboardInterrupt):
        return default


# ─────────────────────────────────────────────────────────────────────────────
#  Step 1 — University URL + interface detection
# ─────────────────────────────────────────────────────────────────────────────

async def do_university_setup() -> tuple[str, str]:
    """
    Ask for the Blackboard URL, detect interface (Ultra/Classic), save to .env.
    Returns (base_url, interface) where interface is 'ultra' or 'classic'.
    """
    # ── 1) CLI override (--url) takes precedence over everything ──────────
    if _CLI_ARGS.get("url"):
        raw = _CLI_ARGS["url"].strip().rstrip("/")
        if not raw.startswith("http"):
            raw = "https://" + raw
        if not re.fullmatch(r"https?://[a-zA-Z0-9.\-]+(:\d+)?(/[a-zA-Z0-9._\-/]*)?", raw):
            error_msg(f"--url '{raw}' is not a valid URL.")
            sys.exit(2)
        base_url = raw
        console.print(f"  Using URL from --url flag: [cyan]{base_url}[/cyan]")

    else:
        # ── 2) Already configured — offer to keep ─────────────────────────
        existing_url = _read_env_value("BB_BASE_URL")
        if existing_url and re.fullmatch(
            r"https?://[a-zA-Z0-9.\-]+(:\d+)?(/[a-zA-Z0-9._\-/]*)?", existing_url
        ):
            console.print(f"  Current Blackboard URL: [cyan]{existing_url}[/cyan]")
            change = safe_confirm("  Change it?", default=False)
            if not change:
                interface = _read_env_value("BB_INTERFACE") or "ultra"
                return existing_url, interface

        console.print("  Enter your university's Blackboard URL.")
        console.print("  [dim]Examples:  https://blackboard.myuniversity.edu  |  https://learn.myuni.edu.au[/dim]")
        console.print()

        # ── 3) Interactive prompt with strict validation ──────────────────
        while True:
            raw = safe_prompt("  [bold]Blackboard URL[/bold]").strip().rstrip("/")
            if not raw.startswith("http"):
                raw = "https://" + raw
            # Strict: anchored, no whitespace/newlines (prevents .env injection)
            if re.fullmatch(r"https?://[a-zA-Z0-9.\-]+(:\d+)?(/[a-zA-Z0-9._\-/]*)?", raw):
                base_url = raw
                break
            warn("That doesn't look like a valid URL. Please try again.")

    console.print()
    info(f"Detecting Blackboard interface at [cyan]{base_url}[/cyan] ...")

    interface = await _detect_interface(base_url)
    if interface == "ultra":
        success("Blackboard [bold]Ultra[/bold] interface detected 🎨")
    else:
        success("Blackboard [bold]Classic[/bold] interface detected 📚")

    # Save to .env
    _write_env({"BB_BASE_URL": base_url, "BB_INTERFACE": interface})
    info(f"Saved to [dim]{ENV_FILE}[/dim]")

    return base_url, interface


async def _detect_interface(base_url: str) -> str:
    """
    Try loading the Ultra landing page — if it responds with Ultra content, return 'ultra'.
    Otherwise return 'classic'.
    """
    import httpx
    ultra_url = f"{base_url}/ultra/institution-page"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(ultra_url)
            final = str(resp.url)
            if "/ultra/" in final and base_url.split("//")[-1].split("/")[0] in final:
                return "ultra"
    except Exception:
        pass
    return "classic"


def _read_env_value(key: str) -> str | None:
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


def _write_env(values: dict[str, str]) -> None:
    """Write/update key=value pairs in the .env file."""
    existing: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                existing[k.strip()] = v.strip()
    existing.update(values)
    lines = [f"{k}={v}" for k, v in existing.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Step 2 — Interactive browser login
# ─────────────────────────────────────────────────────────────────────────────

async def do_login(interface: str) -> dict[str, str]:
    # Reload config after .env was written
    import importlib

    import config as cfg_module
    importlib.reload(cfg_module)
    import blackboard.auth as auth_module
    importlib.reload(auth_module)

    from blackboard.auth import interactive_login

    console.print("  A browser window will open — [bold]log in as you normally would.[/bold]")
    console.print("  Works with any SSO, Microsoft, Shibboleth, Google, or MFA.")
    console.print()
    info("Complete the login in the browser. The wizard will detect it and close the browser automatically.")

    cookies = await interactive_login()
    return cookies


# ─────────────────────────────────────────────────────────────────────────────
#  Step 3 — Test connection
# ─────────────────────────────────────────────────────────────────────────────

async def do_test() -> bool:
    import importlib

    import blackboard.auth as auth_module
    import blackboard.client as client_module
    importlib.reload(client_module)

    from blackboard.client import BlackboardClient

    info("Testing connection to Blackboard REST API...")

    client = BlackboardClient()
    client._cookies = auth_module.load_cached_cookies() or {}
    client._build_client()

    profile = await client.get_user_profile()
    if profile:
        success(f"Logged in as: [bold]{profile.full_name}[/bold]  (id: {profile.username})")
    else:
        warn("Could not fetch profile — REST API may need admin approval at your university.")
        info("The server will fall back to web scraping. Most features will still work.")

    courses = await client.get_courses()
    if courses:
        success(f"Found [bold]{len(courses)}[/bold] enrolled course(s):")
        for c in courses[:5]:
            console.print(f"     [cyan]•[/cyan] {c.name} [dim]({c.course_id})[/dim]")
        if len(courses) > 5:
            console.print(f"     [dim]  … and {len(courses) - 5} more[/dim]")
    else:
        warn("No courses found. Check your enrolments on the Blackboard website.")

    await client.close()
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  Step 4 — Keychain (optional auto-relogin)
# ─────────────────────────────────────────────────────────────────────────────

def do_keychain() -> None:
    console.print("  You already logged in via the browser above. \u2705")
    console.print()
    console.print("  University sessions expire every few days. When that happens you have two options:")
    console.print()
    console.print("  [bold]Option A[/bold] — [green]Browser re-opens automatically[/green] [dim](recommended \u2014 no password needed)[/dim]")
    info("When your session expires, a browser window will open and you log in again.")
    info("Nothing is stored. Simple and secure.")
    console.print()
    console.print("  [bold]Option B[/bold] — [cyan]Save password in system keychain[/cyan]")
    info("Fully silent background relogin \u2014 no browser popup ever.")
    info("Password stored by OS keychain (macOS Keychain / Windows Credential Manager / Linux Secret Service).")
    console.print()

    # Honour --no-keychain / --yes flags first; otherwise prompt (TTY-safe).
    if _CLI_ARGS.get("no_keychain") or _CLI_ARGS.get("yes"):
        save = False
    else:
        save = safe_confirm(
            "  Save password to Keychain for fully silent relogin? (No = browser reopens when needed)",
            default=False,
        )

    if save:
        console.print()
        username = safe_prompt("  [bold]Username / Student Number[/bold]")
        try:
            password = getpass.getpass("  Password (hidden): ")
        except EOFError:
            warn("No password entered — skipping keychain save.")
            return

        from blackboard.auth import save_credentials_to_keychain
        ok = save_credentials_to_keychain(username.strip(), password.strip())
        if ok:
            success("Password saved to system keychain \u2014 relogin will be fully automatic.")
            info("To remove it later:  python3 setup.py --reset")
        else:
            warn("Keychain save failed \u2014 browser will reopen when your session expires.")
    else:
        success("No problem \u2014 a browser window will open automatically when your session expires.")


# ─────────────────────────────────────────────────────────────────────────────
#  Step 5 — Configure Claude Desktop
# ─────────────────────────────────────────────────────────────────────────────

# ── MCP client config locations ──────────────────────────────────────────────
#
# Each entry: (display_name, config_path, config_format)
#
# config_format:
#   "mcpServers"  → {"mcpServers": {"name": {entry}}}   (Claude Desktop / Code / Cursor / Zed)
#   "mcpServers"  is the same JSON shape for all clients below — only the file path differs.
#
# Paths are checked per OS in _get_mcp_clients().

def _get_mcp_clients() -> list[tuple[str, Path]]:
    """Return (name, config_path) for every MCP client, filtered to the current OS."""
    H = Path.home()
    OS = sys.platform  # "darwin", "linux", "win32"

    clients: list[tuple[str, Path]] = []

    # ── Claude Desktop ────────────────────────────────────────────────────────
    if OS == "darwin":
        clients.append(("Claude Desktop", H / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"))
    elif OS == "win32":
        appdata = Path(os.environ.get("APPDATA", H / "AppData" / "Roaming"))
        clients.append(("Claude Desktop", appdata / "Claude" / "claude_desktop_config.json"))
    else:  # Linux / WSL
        clients.append(("Claude Desktop", H / ".config" / "Claude" / "claude_desktop_config.json"))

    # ── Claude Code (CLI) — top-level mcpServers in ~/.claude.json works ─────
    # Verified empirically: writing {"mcpServers": {...}} at the top level of
    # ~/.claude.json is picked up by Claude Code as a user-scope server, even
    # though the file also stores per-project state.
    clients.append(("Claude Code", H / ".claude.json"))

    # NOTE: Codex CLI is intentionally NOT auto-configured.
    # It uses TOML at ~/.codex/config.toml (not JSON); surfaced as manual
    # instructions at end of wizard.

    # ── Cursor ────────────────────────────────────────────────────────────────
    clients.append(("Cursor", H / ".cursor" / "mcp.json"))

    # ── Windsurf ──────────────────────────────────────────────────────────────
    clients.append(("Windsurf", H / ".codeium" / "windsurf" / "mcp_config.json"))

    # ── Zed ───────────────────────────────────────────────────────────────────
    if OS == "darwin":
        clients.append(("Zed", H / "Library" / "Application Support" / "Zed" / "settings.json"))
    elif OS == "linux":
        clients.append(("Zed", H / ".config" / "zed" / "settings.json"))

    # ── Continue ──────────────────────────────────────────────────────────────
    clients.append(("Continue", H / ".continue" / "config.json"))

    # ── Gemini CLI ────────────────────────────────────────────────────────────
    clients.append(("Gemini CLI", H / ".gemini" / "settings.json"))

    # ── Cline (VS Code extension) ─────────────────────────────────────────────
    if OS == "darwin":
        clients.append(("Cline", H / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"))
    elif OS == "linux":
        clients.append(("Cline", H / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"))
    elif OS == "win32":
        appdata = Path(os.environ.get("APPDATA", H / "AppData" / "Roaming"))
        clients.append(("Cline", appdata / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"))

    return clients


def _write_mcp_config(config_path: Path, server_name: str, entry: dict) -> None:
    """
    Write the server entry into a JSON config file.
    Handles the two shapes used across MCP clients:
      - Standard:  {"mcpServers": {name: entry}}
      - Zed:       {"context_servers": {name: {"command": ..., "settings": {}}}}
      - Continue:  {"mcpServers": {name: entry}}  (same as standard)
    """
    config: dict = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config = {}

    # Zed uses a different key and schema
    if "zed" in str(config_path).lower():
        servers = config.setdefault("context_servers", {})
        # Migrate: remove any legacy "blackboard-<slug>" entries from previous versions
        for stale in [k for k in list(servers) if k.startswith("blackboard-")]:
            del servers[stale]
        servers[server_name] = {
            "command": {
                "path": entry["command"],
                "args": entry["args"],
            },
            "settings": {},
        }
    else:
        servers = config.setdefault("mcpServers", {})
        # Migrate: remove any legacy "blackboard-<slug>" entries from previous versions
        for stale in [k for k in list(servers) if k.startswith("blackboard-")]:
            del servers[stale]
        servers[server_name] = entry

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def do_claude_config(base_url: str) -> None:
    # Universal server name — same for every user, every university.
    # The URL is in .env, so there's no need to leak the school name here.
    server_name = "blackboard"

    entry = {
        "command": PYTHON,
        "args": [str(PROJECT_DIR / "server.py")],
        "cwd": str(PROJECT_DIR),
    }

    configured: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for client_name, config_path in _get_mcp_clients():
        if not config_path.parent.exists():
            skipped.append(client_name)
            continue
        try:
            _write_mcp_config(config_path, server_name, entry)
            configured.append(client_name)
        except Exception as exc:
            failed.append(f"{client_name} ({exc})")

    console.print()
    if configured:
        success(f"Server [cyan]{server_name}[/cyan] added to:")
        for name in configured:
            console.print(f"     [green]•[/green] {name}")
    if skipped:
        console.print()
        info(f"Not detected (skipped): {', '.join(skipped)}")
    if failed:
        console.print()
        for f in failed:
            warn(f"Could not configure: {f}")
    console.print()
    warn("[bold]Restart any configured apps[/bold] to activate the MCP server.")

    # Surface manual-only clients that we can't safely auto-configure.
    console.print()
    console.print("[bold]Manual setup for Codex CLI:[/bold]  add this to [cyan]~/.codex/config.toml[/cyan]:")
    console.print(f"  [dim][mcp_servers.{server_name}][/dim]")
    console.print(f'  [dim]command = "{PYTHON}"[/dim]')
    console.print(f'  [dim]args = ["{PROJECT_DIR / "server.py"}"][/dim]')


# ─────────────────────────────────────────────────────────────────────────────
#  Utility flags
# ─────────────────────────────────────────────────────────────────────────────

def handle_clear_keychain() -> None:
    from blackboard.auth import clear_cookie_cache, delete_credentials_from_keychain
    banner()
    console.print("[bold red]Clearing saved data...[/bold red]\n")
    delete_credentials_from_keychain()
    clear_cookie_cache()
    success("Keychain credentials removed.")
    success("Session cache cleared.")
    console.print()
    info("Run [bold]python3 setup.py[/bold] to set up again.")


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def _parse_cli_args() -> None:
    """Populate _CLI_ARGS from sys.argv. Lightweight — no argparse dep needed."""
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--url" and i + 1 < len(args):
            _CLI_ARGS["url"] = args[i + 1]
            i += 2
            continue
        if a.startswith("--url="):
            _CLI_ARGS["url"] = a.split("=", 1)[1]
        elif a in ("-y", "--yes"):
            _CLI_ARGS["yes"] = True
        elif a == "--no-keychain":
            _CLI_ARGS["no_keychain"] = True
        elif a in ("-h", "--help"):
            print(
                "Blackboard MCP setup\n\n"
                "Usage: python3 setup.py [options]\n\n"
                "Options:\n"
                "  --url <URL>        Your university Blackboard URL (skips prompt)\n"
                "  -y, --yes          Accept all default prompts (non-interactive)\n"
                "  --no-keychain      Skip the keychain save step\n"
                "  --reset            Clear saved cookies and keychain creds\n"
                "  --clear-keychain   Same as --reset\n"
                "  -h, --help         Show this help"
            )
            sys.exit(0)
        i += 1


async def main() -> None:
    _parse_cli_args()

    if "--clear-keychain" in sys.argv or "--reset" in sys.argv:
        handle_clear_keychain()
        return

    banner()

    total_steps = 5

    # ── Step 1: University URL ───────────────────────────────────────────────
    step(1, total_steps, "Your University Blackboard URL")
    try:
        base_url, interface = await do_university_setup()
    except Exception as e:
        error_msg(f"URL setup failed: {e}")
        sys.exit(1)

    console.print()

    # ── Step 2: Login ────────────────────────────────────────────────────────
    step(2, total_steps, "Log in to Blackboard")
    try:
        await do_login(interface)
        success("Session captured and cached.")
    except Exception as e:
        error_msg(f"Login failed: {e}")
        info("Make sure you're connected to the internet and your Blackboard URL is correct.")
        sys.exit(1)

    console.print()

    # ── Step 3: Test ─────────────────────────────────────────────────────────
    step(3, total_steps, "Test your connection")
    try:
        await do_test()
    except Exception as e:
        warn(f"Connection test had issues: {e}")
        info("The server may still work — continuing setup.")

    console.print()

    # ── Step 4: Keychain ─────────────────────────────────────────────────────
    step(4, total_steps, "Auto-relogin (optional)")
    do_keychain()

    console.print()

    # ── Step 5: Claude Desktop ───────────────────────────────────────────────
    step(5, total_steps, "Configure Claude Desktop")
    do_claude_config(base_url)

    console.print()

    # ── Done ─────────────────────────────────────────────────────────────────
    console.print(Panel.fit(
        "[bold green]🎉  All done! Blackboard MCP is ready.[/bold green]\n\n"
        "[bold]Restart your AI assistant, then try asking:[/bold]\n\n"
        '  [cyan]"What courses am I enrolled in?"[/cyan]\n'
        '  [cyan]"What assignments are due this week?"[/cyan]\n'
        '  [cyan]"Catch me up on everything in Blackboard"[/cyan]',
        border_style="green",
        padding=(1, 4),
    ))
    console.print()


if __name__ == "__main__":
    asyncio.run(main())
