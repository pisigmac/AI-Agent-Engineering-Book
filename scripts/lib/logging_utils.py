"""Structured console logging helpers."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

console = Console(stderr=True)


def setup_logging(verbose: bool = False, name: str = "book") -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
        force=True,
    )
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "book")


def die(message: str, code: int = 1) -> None:
    console.print(f"[bold red]ERROR:[/bold red] {message}")
    sys.exit(code)
