#!/usr/bin/env python3
"""Genera candidatos de revisión a partir de señales multimodales ya extraídas."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def signal_level(value: float, values: list[float]) -> str:
    ordered = sorted(values)
    if not ordered:
        return "SIN_DATOS"
    low = ordered[round((len(ordered) - 1) * 0.33)]
    high = ordered[round((len(ordered) - 1) * 0.67)]
    if value >= high:
        return "ALTA"
    if value >= low:
        return "MEDIA"
    return "BAJA"


def load_tasks(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def generate(session_id: str, output: Path | None, overwrite: bool) -> Path:
    session_dir = ROOT / "dataset" / "sessions" / session_id
    tasks_path = session_dir / "annotations" / "review" / "annotation_tasks.tsv"
    if not tasks_path.exists():
        raise FileNotFoundError(f"Falta la cola de revisión: {tasks_path}")

    tasks = load_tasks(tasks_path)
    if not tasks:
        raise ValueError("La cola de revisión no contiene ventanas")

    rms_values = [float(task["rms_mean"]) for task in tasks]
    motion_values = [float(task["motion_mean"]) for task in tasks]
    priority_values = [float(task["priority_score"]) for task in tasks]
    candidates = []
    for task in tasks:
        rms = float(task["rms_mean"])
        motion = float(task["motion_mean"])
        priority = float(task["priority_score"])
        candidates.append({
            "candidate_id": task["task_id"],
            "window": {
                "start_seconds": float(task["start_seconds"]),
                "end_seconds": float(task["end_seconds"]),
            },
            "review_status": "needs_expert_review",
            "signals": {
                "audio_activity": {
                    "level": signal_level(rms, rms_values),
                    "rms_mean": rms,
                    "zcr_mean": float(task["zcr_mean"]),
                    "review_focus": "Confirmar si hay voz, música, silencio u otro sonido observable.",
                },
                "visual_motion": {
                    "level": signal_level(motion, motion_values),
                    "motion_mean": motion,
                    "motion_peak": float(task["motion_peak"]),
                    "review_focus": "Confirmar actor, tipo de movimiento u objeto; descartar movimiento de cámara.",
                },
                "multimodal_coincidence": {
                    "level": signal_level(priority, priority_values),
                    "priority_score": priority,
                    "priority_rank": int(task["priority_rank"]),
                    "review_focus": "Revisar si audio y movimiento coinciden en una interacción observable.",
                },
            },
        })

    destination = output or session_dir / "annotations" / "preannotations" / "v1_signal_candidates.json"
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Ya existe {destination}; usa --sobrescribir para regenerarlo")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_id": session_id,
        "generator": "feature-based-preannotation-v1",
        "source": {
            "review_queue": str(tasks_path.relative_to(session_dir)),
            "audio_features": "processed/features/audio_features.json",
            "visual_features": "processed/features/visual_motion.json",
        },
        "review_required": True,
        "ground_truth": False,
        "clinical_assessment": False,
        "limitations": [
            "Los niveles se derivan de señales agregadas, no de reconocimiento semántico.",
            "No identifican participantes, instrumentos, voz, mirada ni interacción clínica.",
            "No son eventos canónicos ni puntuaciones DEMUCA.",
        ],
        "candidates": candidates,
    }
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera candidatos de revisión multimodal")
    parser.add_argument("session_id")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--sobrescribir", action="store_true")
    args = parser.parse_args()
    try:
        output = generate(args.session_id, args.out, args.sobrescribir)
    except (FileNotFoundError, FileExistsError, ValueError, KeyError) as error:
        parser.exit(1, f"[ERROR] {error}\n")
    print(f"[OK] Preanotaciones generadas: {output}")


if __name__ == "__main__":
    main()
