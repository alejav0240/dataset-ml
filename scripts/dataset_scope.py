"""Shared dataset inclusion rules for validation and reporting."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "dataset.yaml"


def excluded_session_ids() -> set[str]:
    """Return explicitly excluded local fixtures without deleting their files."""
    if not CONFIG_FILE.exists():
        return set()
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    sessions = config.get("sesiones", {})
    return set(sessions.get("excluidas", []))


def included_session_dirs(sessions_dir: Path) -> tuple[list[Path], list[str]]:
    """Return production sessions and excluded directory names in stable order."""
    excluded = excluded_session_ids()
    sessions = []
    excluded_found = []
    for path in sorted(sessions_dir.iterdir()):
        if not path.is_dir():
            continue
        if path.name in excluded:
            excluded_found.append(path.name)
        else:
            sessions.append(path)
    return sessions, excluded_found
