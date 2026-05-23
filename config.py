"""
config.py — Settings for Blackboard MCP.

Works with ANY university that uses Blackboard Learn (Ultra or Classic).

On first use, run the setup wizard:
    python3 setup.py

Or let the MCP server guide you — just ask your AI assistant:
    "Connect my Blackboard account"

Settings are stored in a .env file in this directory.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BB_",
        extra="ignore",
    )

    # Your university's Blackboard URL — set by the setup wizard or connect_blackboard tool.
    # Example: https://blackboard.myuniversity.edu
    # Leave empty to be guided through setup on first use.
    base_url: str = ""

    # Blackboard interface version: 'ultra' (default) or 'classic'.
    # Auto-detected by the setup wizard.
    interface: str = "ultra"

    # Where to cache session cookies between server restarts.
    # Stored in your home directory, never inside the repo.
    session_cache: str = "~/.bb_mcp_session.json"

    # Set to true to suppress the browser window during auto-login (Keychain mode).
    headless: bool = True

    def is_configured(self) -> bool:
        """Return True if a Blackboard URL has been set."""
        return bool(self.base_url and self.base_url.startswith("http"))


settings = Settings()
