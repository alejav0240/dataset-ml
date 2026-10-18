#!/usr/bin/env python3
"""Audita cobertura, procesamiento y preparación para entrenamiento del dataset."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_DIR = ROOT / "dataset" / "sessions"
MODALITIES = ("visual", "audio", "interaction")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def numeric_summary(values: list[float]) -> dict:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min": min(values),
        "mean": round(statistics.fmean(values), 6),
        "median": round(statistics.median(values), 6),
        "max": max(values),
    }


def analyze_session(session_dir: Path) -> dict:
    metadata_path = session_dir / "metadata" / "session.json"
    result = {
        "session_id": session_dir.name,
        "structurally_complete": metadata_path.exists(),
        "processing_complete": False,
        "annotation_counts": {},
        "example_annotations": 0,
        "real_annotations": 0,
        "event_types": {},
        "features": {},
        "warnings": [],
    }
    if not metadata_path.exists():
        result["warnings"].append("Falta metadata/session.json")
        result["training_ready"] = False
        return result

    metadata = load_json(metadata_path)
    result["duration_seconds"] = metadata.get("technical", {}).get("duration_seconds")
    processing = metadata.get("processing", {})
    result["processing_complete"] = all(
        processing.get(key) is True
        for key in ("video_processed", "audio_processed", "frames_extracted", "features_extracted")
    )

    for modality in MODALITIES:
        path = session_dir / "annotations" / modality / "events.json"
        events = load_json(path).get("events", []) if path.exists() else []
        examples = sum(event.get("es_ejemplo") is True for event in events)
        result["annotation_counts"][modality] = len(events)
        result["example_annotations"] += examples
        result["real_annotations"] += len(events) - examples
        result["event_types"][modality] = dict(sorted(Counter(
            event.get("type", "SIN_TIPO") for event in events
        ).items()))

    demuca_path = session_dir / "annotations" / "demuca" / "evaluations.json"
    evaluations = load_json(demuca_path).get("evaluations", []) if demuca_path.exists() else []
    example_evaluations = sum(item.get("es_ejemplo") is True for item in evaluations)
    result["annotation_counts"]["demuca_evaluations"] = len(evaluations)
    result["annotation_counts"]["demuca_responses"] = sum(
        len(item.get("responses", [])) for item in evaluations
    )
    result["example_annotations"] += example_evaluations
    result["real_annotations"] += len(evaluations) - example_evaluations

    feature_specs = (
        ("audio_features.json", "rms_energy"),
        ("audio_features.json", "zero_crossing_rate"),
        ("visual_motion.json", "motion_intensity"),
    )
    for filename, key in feature_specs:
        path = session_dir / "processed" / "features" / filename
        values = load_json(path).get(key, []) if path.exists() else []
        result["features"][key] = numeric_summary(values)

    result["frame_count"] = len(list((session_dir / "processed" / "frames").glob("*.jpg")))
    if not result["processing_complete"]:
        result["warnings"].append("Pipeline de procesamiento incompleto")
    if result["real_annotations"] == 0:
        result["warnings"].append("No contiene anotaciones reales; solo ejemplos o archivos vacíos")
    if result["example_annotations"]:
        result["warnings"].append(
            f"Contiene {result['example_annotations']} anotaciones/evaluaciones marcadas como ejemplo"
        )

    result["training_ready"] = (
        result["processing_complete"] and result["real_annotations"] > 0
    )
    return result


def analyze_dataset() -> dict:
    sessions = [analyze_session(path) for path in sorted(SESSIONS_DIR.iterdir()) if path.is_dir()]
    durations = [item["duration_seconds"] for item in sessions if item.get("duration_seconds")]
    return {
        "dataset": "DEMUCA multimodal",
        "sessions_total": len(sessions),
        "sessions_processed": sum(item["processing_complete"] for item in sessions),
        "sessions_training_ready": sum(item["training_ready"] for item in sessions),
        "annotated_duration_seconds": round(sum(durations), 3),
        "sessions": sessions,
    }


def print_report(report: dict) -> None:
    print("=" * 58)
    print("ANÁLISIS DEL DATASET DEMUCA")
    print("=" * 58)
    print(f"Sesiones detectadas:       {report['sessions_total']}")
    print(f"Sesiones procesadas:       {report['sessions_processed']}")
    print(f"Listas para entrenamiento: {report['sessions_training_ready']}")
    print(f"Duración con medios:       {report['annotated_duration_seconds'] / 60:.2f} min")
    for session in report["sessions"]:
        print(f"\n[{session['session_id']}] procesada={session['processing_complete']} "
              f"lista={session['training_ready']}")
        print(f"  eventos: {session['annotation_counts']}")
        print(f"  reales={session['real_annotations']}, ejemplos={session['example_annotations']}, "
              f"frames={session.get('frame_count', 0)}")
        for warning in session["warnings"]:
            print(f"  [ADVERTENCIA] {warning}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analiza cobertura y preparación del dataset")
    parser.add_argument("--json", action="store_true", help="Imprime el informe como JSON")
    parser.add_argument("--out", type=Path, help="Guarda el informe JSON en esta ruta")
    args = parser.parse_args()
    report = analyze_dataset()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[OK] Informe guardado en {args.out}")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
