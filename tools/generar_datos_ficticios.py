#!/usr/bin/env python3
"""Rellena las sesiones de demostracion con datos sinteticos coherentes."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_DIR = ROOT / "dataset" / "sessions"
REAL_SESSIONS = {"S001"}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def event(start: float, end: float, event_type: str, **extra: object) -> dict:
    return {
        "start_seconds": start,
        "end_seconds": end,
        "type": event_type,
        "source": "synthetic_demo_v1",
        "es_ejemplo": True,
        **extra,
    }


def metadata(session_id: str, number: int, duration: int) -> dict:
    patient_id = f"P{number:03d}"
    therapist_id = f"T{(number % 4) + 1:03d}"
    return {
        "session_id": session_id,
        "dataset_version": "0.1.0",
        "data_origin": "synthetic_demo",
        "synthetic_data": True,
        "participants": [
            {"id": patient_id, "role": "PACIENTE"},
            {"id": therapist_id, "role": "TERAPEUTA"},
        ],
        "recording": {
            "original_video": f"raw/original/{session_id}_synthetic.mp4",
            "audio": f"raw/audio/{session_id}_synthetic.wav",
            "video_only": f"raw/video/{session_id}_synthetic_video.mp4",
        },
        "technical": {
            "duration_seconds": duration,
            "video_fps": 10,
            "video_width": 1280,
            "video_height": 720,
            "audio_sample_rate": 16000,
            "audio_channels": 1,
        },
        "processing": {
            "video_processed": False,
            "audio_processed": False,
            "frames_extracted": False,
            "features_extracted": True,
        },
        "annotation": {
            "visual": True,
            "audio": True,
            "interaction": True,
            "demuca": True,
        },
        "quality": {
            "video_quality": "SIMULADA_BUENA",
            "audio_quality": "SIMULADA_BUENA",
            "occlusion": "SIMULADA_BAJA",
            "background_noise": "SIMULADO_BAJO",
        },
    }


def annotations(session_id: str, number: int, duration: int) -> dict[str, dict]:
    patient_id = f"P{number:03d}"
    therapist_id = f"T{(number % 4) + 1:03d}"
    rng = random.Random(number)

    def interval(index: int, total: int) -> tuple[float, float]:
        center = (index + 1) * duration / (total + 1) + rng.uniform(-25, 25)
        start = max(5, round(center - rng.uniform(3, 12), 1))
        end = min(duration - 2, round(start + rng.uniform(4, 35), 1))
        return start, end

    def synthetic_source() -> str:
        return rng.choice(("synthetic_preannotation_v1", "synthetic_observation_v1"))

    # S001 is dominated by movement and musical activity. The synthetic sessions retain
    # that tendency while varying event volume, type, timing and attributes per session.
    visual = []
    for index in range(rng.randint(5, 10)):
        start, end = interval(index, 10)
        event_type = rng.choices(
            ("MOVIMIENTO", "INTERACCION_OBJETO", "MOVIMIENTO_REPETITIVO", "CONTACTO_VISUAL", "ORIENTACION_CORPORAL"),
            weights=(48, 20, 14, 10, 8),
        )[0]
        extra: dict[str, object] = {"participant": patient_id, "source": synthetic_source()}
        if event_type == "MOVIMIENTO":
            extra["attributes"] = {
                "intensidad": rng.choice(("BAJO", "MEDIO", "MEDIO", "ALTO")),
                "parte_cuerpo": rng.choice(("BRAZO", "MANO", "TORSO", "CUERPO_ENTERO")),
            }
        elif event_type == "INTERACCION_OBJETO":
            extra["attributes"] = {
                "accion": rng.choice(("TOCAR", "AGARRAR", "MOVER", "USAR")),
                "tipo_objeto": rng.choice(("TAMBOR", "GUITARRA", "PIANO", "MARACA")),
            }
        elif event_type == "MOVIMIENTO_REPETITIVO":
            extra["attributes"] = {
                "type": rng.choice(("MANO", "BRAZO", "CABEZA")),
                "frecuencia": rng.choice(("BAJA", "MEDIA", "MEDIA", "ALTA")),
            }
        elif event_type == "CONTACTO_VISUAL":
            extra["attributes"] = {"objetivo": rng.choice(("TERAPEUTA", "OBJETO", "TERAPEUTA"))}
        visual.append(event(start, end, event_type, **extra))

    audio = []
    for index in range(rng.randint(4, 9)):
        start, end = interval(index, 9)
        event_type = rng.choices(
            ("ACTIVIDAD_MUSICAL", "VOCALIZACION", "RISA", "HABLA", "SILENCIO"),
            weights=(52, 20, 10, 10, 8),
        )[0]
        extra = {"source": synthetic_source()}
        if event_type == "ACTIVIDAD_MUSICAL":
            extra["speaker"] = rng.choice((therapist_id, therapist_id, patient_id))
            extra["attributes"] = {"type": rng.choice(("TERAPEUTA_TOCANDO", "PACIENTE_TOCANDO", "TOCANDO_JUNTOS", "CANTO"))}
        elif event_type == "VOCALIZACION":
            extra["speaker"] = patient_id
            extra["attributes"] = {"type": rng.choice(("VOCALIZACION", "BALBUCEO", "HABLA"))}
        elif event_type in ("RISA", "HABLA"):
            extra["speaker"] = rng.choice((patient_id, therapist_id))
        audio.append(event(start, end, event_type, **extra))

    interaction = []
    for index in range(rng.randint(3, 7)):
        start, end = interval(index, 7)
        event_type = rng.choices(
            ("ACTIVIDAD_CONJUNTA", "RESPUESTA", "IMITACION", "MIRADA", "INTERACCION_MUSICAL"),
            weights=(35, 28, 15, 12, 10),
        )[0]
        extra = {"source": synthetic_source()}
        if event_type in ("RESPUESTA", "IMITACION", "MIRADA"):
            extra["participant"] = patient_id
        else:
            extra["participants"] = [patient_id, therapist_id]
        interaction.append(event(start, end, event_type, **extra))

    subscales = [
        ("Estereotipias", "Comportamientos Restrictivos", "visual"),
        ("Desinterés", "Comportamientos Restrictivos", "visual"),
        ("Aislamiento", "Comportamientos Restrictivos", "interaction"),
        ("Contacto Visual", "Interacción Social y Cognición", "visual"),
        ("Vocalizaciones", "Exploración Vocal", "audio"),
        ("Balbuceos", "Exploración Vocal", "audio"),
        ("Creación Vocal", "Exploración Vocal", "audio"),
        ("Interacción con Instrumentos", "Interacción Social y Cognición", "interaction"),
        ("Pulso Interno", "Percepción y Exploración Rítmica", "audio"),
        ("Interacción con Educador / Musicoterapeuta", "Interacción Social y Cognición", "interaction"),
        ("Atención", "Interacción Social y Cognición", "visual"),
        ("Imitación", "Interacción Social y Cognición", "interaction"),
        ("Regulación Temporal", "Percepción y Exploración Rítmica", "audio"),
        ("Movimiento Sonoro", "Percepción y Exploración Sonora", "audio"),
    ]
    score_weights = {
        "Comportamientos Restrictivos": (0, 1, 1, 2),
        "Exploración Vocal": (1, 1, 2, 2),
        "Interacción Social y Cognición": (1, 2, 2, 2),
        "Percepción y Exploración Rítmica": (0, 1, 1, 2),
        "Percepción y Exploración Sonora": (1, 2, 2),
    }
    responses = []
    modality_events = {"visual": visual, "audio": audio, "interaction": interaction}
    for subscale, category, modality in subscales:
        evidence_event = rng.choice(modality_events[modality])
        score = rng.choice(score_weights[category])
        responses.append({
            "subscale": subscale,
            "category": category,
            "score": score,
            "max_score": 2,
            "evidence": [{
                "modality": modality,
                "start_seconds": evidence_event["start_seconds"],
                "end_seconds": evidence_event["end_seconds"],
                "description": "Evidencia sintetica inspirada en la distribucion observada de S001; requiere revision clinica.",
            }],
        })
    evaluation = {
        "scale": "Escala DEMUCA",
        "scale_type": "subscale",
        "patient_id": patient_id,
        "evaluator_id": therapist_id,
        "evaluated_at": "2026-10-07",
        "review_status": "synthetic_demo",
        "es_ejemplo": True,
        "ground_truth": False,
        "responses": responses,
        "total_score": sum(response["score"] for response in responses),
        "max_total_score": len(responses) * 2,
        "notes": "Evaluacion sintetica creada solo para pruebas de interfaz y EDA.",
    }
    return {
        "visual": {"session_id": session_id, "data_origin": "synthetic_demo", "events": visual},
        "audio": {"session_id": session_id, "data_origin": "synthetic_demo", "events": audio},
        "interaction": {"session_id": session_id, "data_origin": "synthetic_demo", "events": interaction},
        "demuca": {"session_id": session_id, "data_origin": "synthetic_demo", "evaluations": [evaluation]},
    }


def features(session_id: str, number: int, duration: int) -> tuple[dict, dict]:
    rng = random.Random(number * 1000)
    timestamps = [index + 0.5 for index in range(duration)]
    audio_baseline = 0.035 + (number % 6) * 0.004
    motion_baseline = 10 + (number % 7) * 1.8
    rms = [round(max(0.002, audio_baseline + 0.018 * math.sin(timestamp / 47) + rng.gauss(0, 0.011)), 6)
           for timestamp in timestamps]
    zcr = [round(max(0.005, 0.048 + 0.014 * math.cos(timestamp / 71) + rng.gauss(0, 0.006)), 6)
           for timestamp in timestamps]
    motion = [round(max(0, motion_baseline + 9 * math.sin(timestamp / 59) + rng.gauss(0, 5)), 4)
              for timestamp in timestamps]
    return (
        {
            "session_id": session_id,
            "data_origin": "synthetic_demo",
            "sample_rate": 16000,
            "window_seconds": 1.0,
            "total_windows": len(timestamps),
            "timestamps": timestamps,
            "rms_energy": rms,
            "zero_crossing_rate": zcr,
        },
        {
            "session_id": session_id,
            "data_origin": "synthetic_demo",
            "sampling_fps": 1.0,
            "total_frames": len(timestamps),
            "timestamps": timestamps,
            "motion_intensity": motion,
        },
    )


def populate_session(session_dir: Path) -> None:
    session_id = session_dir.name
    number = int(session_id[1:])
    duration = 840 + (number % 6) * 90
    write_json(session_dir / "metadata" / "session.json", metadata(session_id, number, duration))
    data = annotations(session_id, number, duration)
    write_json(session_dir / "annotations" / "visual" / "events.json", data["visual"])
    write_json(session_dir / "annotations" / "audio" / "events.json", data["audio"])
    write_json(session_dir / "annotations" / "interaction" / "events.json", data["interaction"])
    write_json(session_dir / "annotations" / "demuca" / "evaluations.json", data["demuca"])
    audio_features, visual_features = features(session_id, number, duration)
    write_json(session_dir / "processed" / "features" / "audio_features.json", audio_features)
    write_json(session_dir / "processed" / "features" / "visual_motion.json", visual_features)


def main() -> None:
    populated = []
    for session_dir in sorted(path for path in SESSIONS_DIR.iterdir() if path.is_dir()):
        if session_dir.name in REAL_SESSIONS:
            continue
        populate_session(session_dir)
        populated.append(session_dir.name)
    print(f"Sesiones sinteticas pobladas: {', '.join(populated)}")


if __name__ == "__main__":
    main()
