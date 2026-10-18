#!/usr/bin/env python3

import json
import sys
from pathlib import Path
import yaml

from jsonschema import validate
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset" / "sessions"
SCHEMA_FILE = ROOT / "schemas" / "session.schema.json"
ANNOTATION_SCHEMA_FILE = ROOT / "config" / "annotation_schema.yaml"


def cargar_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def cargar_yaml(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def validar_annotations(session_dir: Path, session_duration: float | None, ann_schema: dict) -> list[str]:
    errores = []
    session_id = session_dir.name

    # 1. Validar visual, audio, interaction
    for mod in ("visual", "audio", "interaction"):
        ev_file = session_dir / "annotations" / mod / "events.json"
        if not ev_file.exists():
            continue

        try:
            data = cargar_json(ev_file)
        except Exception as e:
            errores.append(f"{mod}/events.json: JSON corrupto ({e})")
            continue

        events = data.get("events", [])
        schema_key = "interaccion" if mod == "interaction" else mod
        schema_mod = ann_schema.get(schema_key, {})

        if data.get("session_id") != session_id:
            errores.append(
                f"{mod}/events.json: session_id '{data.get('session_id')}' no coincide con '{session_id}'"
            )

        for idx, ev in enumerate(events):
            t_start = ev.get("start_seconds")
            t_end = ev.get("end_seconds")
            ev_type = ev.get("type")

            if t_start is None or t_end is None:
                errores.append(f"{mod} evento #{idx}: falta start_seconds o end_seconds")
            elif t_start < 0:
                errores.append(f"{mod} evento #{idx}: start_seconds ({t_start}) < 0")
            elif t_end < t_start:
                errores.append(f"{mod} evento #{idx}: end_seconds ({t_end}) < start_seconds ({t_start})")
            elif session_duration and t_end > (session_duration + 2.0):  # margen de 2s
                errores.append(f"{mod} evento #{idx}: end_seconds ({t_end}s) excede duración de sesión ({session_duration}s)")

            if ev_type and schema_mod and ev_type not in schema_mod:
                errores.append(f"{mod} evento #{idx}: tipo '{ev_type}' no está en annotation_schema.yaml")
                continue
            if not ev_type:
                errores.append(f"{mod} evento #{idx}: falta type")
                continue

            event_schema = schema_mod.get(ev_type, {})
            required_actor = (
                event_schema.get("participante_requerido")
                or event_schema.get("participant_required")
            )
            required_speaker = (
                event_schema.get("hablante_requerido")
                or event_schema.get("speaker_required")
            )
            if required_actor and not ev.get("participant"):
                errores.append(f"{mod} evento #{idx}: '{ev_type}' requiere participant")
            if required_speaker and not ev.get("speaker"):
                errores.append(f"{mod} evento #{idx}: '{ev_type}' requiere speaker")

            attributes = ev.get("attributes", {})
            for attr_name, attr_value in attributes.items():
                attr_schema = event_schema.get("attributes", {}).get(attr_name)
                if not attr_schema:
                    errores.append(
                        f"{mod} evento #{idx}: atributo '{attr_name}' no definido para '{ev_type}'"
                    )
                    continue
                allowed = attr_schema.get("values")
                if allowed and attr_value not in allowed:
                    errores.append(
                        f"{mod} evento #{idx}: valor '{attr_value}' inválido para "
                        f"'{ev_type}.{attr_name}' (permitidos: {', '.join(allowed)})"
                    )

    # 2. Validar demuca
    demuca_file = session_dir / "annotations" / "demuca" / "evaluations.json"
    if demuca_file.exists():
        try:
            d_data = cargar_json(demuca_file)
            if d_data.get("session_id") != session_id:
                errores.append(
                    f"demuca/evaluations.json: session_id '{d_data.get('session_id')}' "
                    f"no coincide con '{session_id}'"
                )
            for eval_item in d_data.get("evaluations", []):
                responses = eval_item.get("responses", [])
                expected_total = sum(resp.get("score", 0) for resp in responses)
                expected_max = sum(resp.get("max_score", 0) for resp in responses)
                if eval_item.get("total_score") != expected_total:
                    errores.append(
                        f"demuca: total_score={eval_item.get('total_score')} no coincide con {expected_total}"
                    )
                if eval_item.get("max_total_score") != expected_max:
                    errores.append(
                        f"demuca: max_total_score={eval_item.get('max_total_score')} no coincide con {expected_max}"
                    )
                for resp in responses:
                    for ev in resp.get("evidence", []):
                        start = ev.get("start_seconds")
                        end = ev.get("end_seconds")
                        if start is not None and end is not None:
                            if end < start:
                                errores.append(f"demuca subescala '{resp.get('subscale')}': end ({end}s) < start ({start}s)")
                            if session_duration and end > (session_duration + 2.0):
                                errores.append(f"demuca subescala '{resp.get('subscale')}': evidencia ({end}s) excede duración ({session_duration}s)")
        except Exception as e:
            errores.append(f"demuca/evaluations.json: JSON corrupto ({e})")

    return errores


def validar_sesion(session_dir: Path, schema: dict, ann_schema: dict) -> bool:
    session_id = session_dir.name
    metadata_file = session_dir / "metadata" / "session.json"

    if not metadata_file.exists():
        print(f"[ERROR] {session_id}: falta metadata/session.json")
        return False

    try:
        metadata = cargar_json(metadata_file)
        validate(instance=metadata, schema=schema)
    except ValidationError as error:
        print(f"[ERROR] {session_id}: metadata inválida")
        print(f"        {error.message}")
        return False
    except json.JSONDecodeError as error:
        print(f"[ERROR] {session_id}: JSON inválido")
        print(f"        {error}")
        return False

    # Validar consistencia temporal y de anotaciones
    duration = metadata.get("technical", {}).get("duration_seconds")
    errores_ann = validar_annotations(session_dir, duration, ann_schema)
    if errores_ann:
        print(f"[ERROR] {session_id}: inconsistencias en anotaciones:")
        for err in errores_ann:
            print(f"        - {err}")
        return False

    # Chequeo de consistencia de flags de procesamiento
    proc = metadata.get("processing", {})
    frames_dir = session_dir / "processed" / "frames"
    has_frames = frames_dir.exists() and any(frames_dir.glob("*.jpg"))
    if has_frames and not proc.get("frames_extracted"):
        print(f"[INFO] {session_id}: frames existen en disco pero 'frames_extracted' es false.")

    print(f"[OK] {session_id}")
    return True


def main():
    if not DATASET_DIR.exists():
        print(f"[ERROR] No existe: {DATASET_DIR}")
        sys.exit(1)

    schema = cargar_json(SCHEMA_FILE)
    ann_schema = cargar_yaml(ANNOTATION_SCHEMA_FILE) if ANNOTATION_SCHEMA_FILE.exists() else {}
    sessions = sorted(path for path in DATASET_DIR.iterdir() if path.is_dir())

    if not sessions:
        print("[WARNING] No existen sesiones")
        return

    validas = sum(validar_sesion(session, schema, ann_schema) for session in sessions)
    print("\n" + "=" * 40)
    print("VALIDACIÓN ESTRUCTURAL DEL DATASET")
    print("=" * 40)
    print(f"Sesiones:  {len(sessions)}")
    print(f"Estructuralmente válidas:   {validas}")
    print(f"Estructuralmente inválidas: {len(sessions) - validas}")
    if validas != len(sessions):
        sys.exit(1)


if __name__ == "__main__":
    main()
