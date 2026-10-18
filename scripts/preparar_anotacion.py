#!/usr/bin/env python3
"""Genera ventanas priorizadas para revisión humana, sin crear etiquetas clínicas."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def values_in_window(timestamps: list[float], values: list[float], start: float, end: float) -> list[float]:
    return [value for timestamp, value in zip(timestamps, values) if start <= timestamp < end]


def minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def prepare(session_id: str, window_seconds: float, output: Path | None, overwrite: bool) -> Path:
    session_dir = ROOT / "dataset" / "sessions" / session_id
    metadata_path = session_dir / "metadata" / "session.json"
    audio_path = session_dir / "processed" / "features" / "audio_features.json"
    motion_path = session_dir / "processed" / "features" / "visual_motion.json"
    for required in (metadata_path, audio_path, motion_path):
        if not required.exists():
            raise FileNotFoundError(f"Falta archivo requerido: {required}")

    metadata = load_json(metadata_path)
    duration = metadata.get("technical", {}).get("duration_seconds")
    if not duration or duration <= 0:
        raise ValueError("La sesión no tiene technical.duration_seconds válido")
    audio = load_json(audio_path)
    motion = load_json(motion_path)

    tasks = []
    for index in range(math.ceil(duration / window_seconds)):
        start = round(index * window_seconds, 3)
        end = round(min((index + 1) * window_seconds, duration), 3)
        rms = values_in_window(audio["timestamps"], audio["rms_energy"], start, end)
        zcr = values_in_window(audio["timestamps"], audio["zero_crossing_rate"], start, end)
        movement = values_in_window(motion["timestamps"], motion["motion_intensity"], start, end)
        tasks.append({
            "task_id": f"{session_id}-W{index + 1:04d}",
            "session_id": session_id,
            "start_seconds": start,
            "end_seconds": end,
            "rms_mean": sum(rms) / len(rms) if rms else 0.0,
            "zcr_mean": sum(zcr) / len(zcr) if zcr else 0.0,
            "motion_mean": sum(movement) / len(movement) if movement else 0.0,
            "motion_peak": max(movement) if movement else 0.0,
        })

    rms_norm = minmax([task["rms_mean"] for task in tasks])
    motion_norm = minmax([task["motion_mean"] for task in tasks])
    peak_norm = minmax([task["motion_peak"] for task in tasks])
    for task, rms, movement, peak in zip(tasks, rms_norm, motion_norm, peak_norm):
        task["priority_score"] = round(0.4 * rms + 0.4 * movement + 0.2 * peak, 6)
    ranked = sorted(tasks, key=lambda task: (-task["priority_score"], task["start_seconds"]))
    for rank, task in enumerate(ranked, 1):
        task["priority_rank"] = rank

    out = output or session_dir / "annotations" / "review" / "annotation_tasks.tsv"
    if out.exists() and not overwrite:
        raise FileExistsError(f"Ya existe {out}; usa --sobrescribir para regenerarlo")
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id", "session_id", "start_seconds", "end_seconds", "priority_rank",
        "priority_score", "rms_mean", "zcr_mean", "motion_mean", "motion_peak",
        "status", "annotator_primary", "reviewer", "guide_version", "guide_status",
        "guide_approved_by", "guide_approved_at", "notes",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for task in sorted(tasks, key=lambda item: item["start_seconds"]):
            task.update({
                "status": "pending", "annotator_primary": "", "reviewer": "",
                "guide_version": "draft-0.1", "guide_status": "pending",
                "guide_approved_by": "", "guide_approved_at": "", "notes": "",
            })
            writer.writerow(task)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara tareas de anotación humana")
    parser.add_argument("session_id")
    parser.add_argument("--ventana", type=float, default=30.0, help="Duración de ventana en segundos")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--sobrescribir", action="store_true")
    args = parser.parse_args()
    if args.ventana <= 0:
        parser.error("--ventana debe ser mayor que cero")
    try:
        output = prepare(args.session_id, args.ventana, args.out, args.sobrescribir)
    except (FileNotFoundError, FileExistsError, ValueError, KeyError) as error:
        parser.exit(1, f"[ERROR] {error}\n")
    print(f"[OK] Cola de anotación creada: {output}")


if __name__ == "__main__":
    main()
