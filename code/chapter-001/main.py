"""Chapter 1 CLI entrypoint — boot the platform scaffold."""

from __future__ import annotations

import logging

from logging_setup import setup_logging
from platform_config import Settings, require_non_secret_summary

logger = logging.getLogger("platform")


def main() -> int:
    settings = Settings.from_env()
    setup_logging(settings.log_level)
    summary = require_non_secret_summary(settings)
    logger.info("platform_boot settings=%s", summary)
    print(f"{settings.app_name} ready in {settings.environment} mode")
    print("Next: Chapter 2 — map the AI engineering stack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
