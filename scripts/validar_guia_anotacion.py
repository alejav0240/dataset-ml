#!/usr/bin/env python3
"""Check that an annotation guide draft is complete and explicitly approved."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GUIDE = PROJECT_ROOT / "dataset" / "GUIA_ANOTACION_TEMPLATE.md"
DEFAULT_TASK_CONFIG = PROJECT_ROOT / "ml" / "task.json"
APPROVAL_FIELDS = (
    "Versión de la guía",
    "Responsable de anotación primaria",
    "Responsable de revisión/adjudicación",
    "Profesional que aprueba los criterios aplicables",
    "Fecha y evidencia de aprobación",
    "Sesiones y modalidades cubiertas",
)


def validate_guide(guide_path: Path, task_config_path: Path) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        guide = guide_path.read_text(encoding="utf-8")
    except OSError as error:
        return {"valid": False, "guide": str(guide_path), "blockers": [f"guide_read_failed:{error}"]}

    try:
        task = json.loads(task_config_path.read_text(encoding="utf-8"))
        expected_labels = {
            label
            for labels in task["label_sources"].values()
            for label in labels
        }
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        return {
            "valid": False,
            "guide": str(guide_path),
            "blockers": [f"task_config_read_failed:{error}"],
        }

    if not re.search(r"^> \*\*Estado de guía: APROBADA\b", guide, re.MULTILINE):
        blockers.append("guide_not_explicitly_approved")
    if "PENDIENTE" in guide:
        blockers.append("guide_has_pending_fields")
    if re.search(r"^- \[ \] ", guide, re.MULTILINE):
        blockers.append("guide_checklist_incomplete")

    for field in APPROVAL_FIELDS:
        match = re.search(rf"^\| {re.escape(field)} \|\s*([^|]*)\|$", guide, re.MULTILINE)
        if not match or not match.group(1).strip():
            blockers.append(f"approval_metadata_missing:{field}")

    guide_labels = set(re.findall(r"^#### `([^`]+)`", guide, re.MULTILINE))
    for label in sorted(expected_labels - guide_labels):
        blockers.append(f"label_definition_missing:{label}")
    for label in sorted(guide_labels - expected_labels):
        blockers.append(f"unknown_label_definition:{label}")

    headings = list(re.finditer(r"^#### `([^`]+)`[^\n]*$", guide, re.MULTILINE))
    required_fields = {
        "operational_rule": re.compile(r"^- Regla operativa aprobada.*:\s*(.*)$"),
        "positive_example": re.compile(r"^- Ejemplo positivo.*:\s*(.*)$"),
        "negative_example": re.compile(r"^- Ejemplo negativo.*:\s*(.*)$"),
        "ambiguous_case": re.compile(r"^- Caso ambiguo.*:\s*(.*)$"),
    }
    for index, heading in enumerate(headings):
        label = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(guide)
        section = guide[heading.end():end]
        for field, pattern in required_fields.items():
            match = next(
                (candidate for line in section.splitlines() if (candidate := pattern.match(line))),
                None,
            )
            if match is None:
                blockers.append(f"label_field_missing:{label}:{field}")
            elif not match.group(1).strip() or "PENDIENTE" in match.group(1):
                blockers.append(f"label_field_incomplete:{label}:{field}")

    return {
        "valid": not blockers,
        "guide": str(guide_path),
        "labels_checked": len(expected_labels),
        "blockers": blockers,
        "notice": "This preflight checks completeness and recorded approval only; it does not approve clinical criteria.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guide", type=Path, default=DEFAULT_GUIDE)
    parser.add_argument("--task-config", type=Path, default=DEFAULT_TASK_CONFIG)
    args = parser.parse_args()
    report = validate_guide(args.guide, args.task_config)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
