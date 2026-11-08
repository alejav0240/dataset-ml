#!/usr/bin/env python3
"""Anotador audiovisual local para el dataset DEMUCA (sin dependencias web)."""

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_DIR = ROOT / "dataset" / "sessions"
SCHEMA_PATH = ROOT / "config" / "annotation_schema.yaml"
STATIC_DIR = Path(__file__).resolve().parent / "anotador_web"
MODALITY_TO_SCHEMA = {"visual": "visual", "audio": "audio", "interaction": "interaccion"}
SESSION_RE = re.compile(r"^S\d{3,}$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def session_dir(session_id: str) -> Path:
    if not SESSION_RE.fullmatch(session_id):
        raise ValueError("Identificador de sesión inválido")
    path = (SESSIONS_DIR / session_id).resolve()
    if path.parent != SESSIONS_DIR.resolve() or not path.is_dir():
        raise ValueError("La sesión no existe")
    return path


def metadata_for(session_id: str) -> dict:
    path = session_dir(session_id) / "metadata" / "session.json"
    if not path.exists():
        raise ValueError("La sesión no tiene metadata/session.json")
    return load_json(path)


def video_for(session_id: str) -> Path:
    base = session_dir(session_id)
    processed = sorted((base / "processed" / "video").glob("*.mp4"))
    if processed:
        return processed[0]
    metadata = metadata_for(session_id)
    relative = metadata.get("recording", {}).get("original_video")
    if not relative:
        raise ValueError("No hay video configurado")
    candidate = (base / relative).resolve()
    if base not in candidate.parents or not candidate.is_file():
        raise ValueError("El video configurado no existe o está fuera de la sesión")
    return candidate


def _has_audio_stream(path: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def preview_video_for(session_id: str) -> Path:
    """Return a browser-compatible preview with normalized audio muxed in."""
    base = session_dir(session_id)
    video = video_for(session_id)
    audio = base / "processed" / "audio" / f"{session_id}_16khz_mono.wav"
    if not audio.is_file() or _has_audio_stream(video):
        return video
    preview = base / "processed" / "video" / f"{session_id}_annotator_preview.mp4"
    if preview.is_file() and preview.stat().st_mtime >= max(video.stat().st_mtime, audio.stat().st_mtime):
        return preview
    preview.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{preview.name}.", suffix=".tmp.mp4", dir=preview.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(video), "-i", str(audio),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-shortest", str(temporary),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"No se pudo agregar el audio al video: {result.stderr.strip()}")
        os.replace(temporary, preview)
        return preview
    finally:
        temporary.unlink(missing_ok=True)


def annotation_path(session_id: str, modality: str) -> Path:
    if modality not in MODALITY_TO_SCHEMA:
        raise ValueError("Modalidad inválida")
    return session_dir(session_id) / "annotations" / modality / "events.json"


def read_events(session_id: str, modality: str) -> dict:
    path = annotation_path(session_id, modality)
    if not path.exists():
        return {"session_id": session_id, "events": []}
    data = load_json(path)
    if data.get("session_id") != session_id or not isinstance(data.get("events"), list):
        raise ValueError(f"Formato inválido en {path}")
    return data


def read_review_tasks(session_id: str) -> list[dict[str, str]]:
    path = session_dir(session_id) / "annotations" / "review" / "annotation_tasks.tsv"
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def read_pose_landmarks(session_id: str) -> dict:
    """Return pose frames for the overlay without assigning identity to a pose."""
    path = session_dir(session_id) / "processed" / "features" / "pose_landmarks.json"
    if not path.is_file():
        return {
            "session_id": session_id,
            "available": False,
            "frames": [],
            "notice": "Esta sesión no tiene un artefacto de pose procesado.",
        }
    payload = load_json(path)
    if payload.get("session_id") != session_id or not isinstance(payload.get("frames"), list):
        raise ValueError("Formato inválido en pose_landmarks.json")
    return {
        "session_id": session_id,
        "available": True,
        "sampling_fps": payload.get("sampling_fps"),
        "landmark_count_per_pose": payload.get("landmark_count_per_pose"),
        "frames": payload["frames"],
        "notice": "Las poses se muestran por índice; MediaPipe no asigna automáticamente paciente o terapeuta.",
    }


def read_review_candidates(session_id: str, task_id: str) -> dict:
    """Read candidate evidence for a known task without promoting it to events."""
    base = session_dir(session_id)
    tasks = read_review_tasks(session_id)
    task = next((row for row in tasks if row.get("task_id") == task_id), None)
    if task is None:
        raise ValueError("La tarea de revisión no existe")

    preannotations = base / "annotations" / "preannotations"
    candidates: dict = {
        "task_id": task_id,
        "ground_truth": False,
        "review_required": True,
        "signal_candidate": None,
        "visual_observations": [],
    }
    signal_path = preannotations / "v1_signal_candidates.json"
    if signal_path.is_file():
        payload = load_json(signal_path)
        candidates["signal_candidate"] = next(
            (item for item in payload.get("candidates", []) if item.get("candidate_id") == task_id),
            None,
        )

    visual_path = preannotations / "v1_visual_observations.json"
    if visual_path.is_file():
        payload = load_json(visual_path)
        observation = next(
            (item for item in payload.get("observations", []) if item.get("candidate_id") == task_id),
            None,
        )
        if observation:
            candidates["visual_observations"] = observation.get("visible_observations", [])
    return candidates


def write_events(session_id: str, modality: str, data: dict) -> None:
    path = annotation_path(session_id, modality)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def public_schema() -> dict:
    raw = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    return {modality: raw.get(schema_key, {}) for modality, schema_key in MODALITY_TO_SCHEMA.items()}


def validate_event(session_id: str, modality: str, event: dict) -> dict:
    if not isinstance(event, dict):
        raise ValueError("El evento debe ser un objeto")
    schema = public_schema()[modality]
    event_type = event.get("type")
    if event_type not in schema:
        raise ValueError(f"Tipo '{event_type}' no permitido para {modality}")
    try:
        start = round(float(event.get("start_seconds")), 3)
        end = round(float(event.get("end_seconds")), 3)
    except (TypeError, ValueError):
        raise ValueError("Inicio y fin deben ser números") from None
    duration = metadata_for(session_id).get("technical", {}).get("duration_seconds")
    if start < 0 or end < start:
        raise ValueError("Los tiempos deben cumplir 0 <= inicio <= fin")
    if duration and end > float(duration) + 2:
        raise ValueError(f"El fin excede la duración de la sesión ({duration:.3f}s)")

    definition = schema[event_type] or {}
    actor_required = definition.get("participante_requerido") or definition.get("participant_required")
    speaker_required = definition.get("hablante_requerido") or definition.get("speaker_required")
    participant = str(event.get("participant") or "").strip()
    speaker = str(event.get("speaker") or "").strip()
    if actor_required and not participant:
        raise ValueError(f"{event_type} requiere participant")
    if speaker_required and not speaker:
        raise ValueError(f"{event_type} requiere speaker")

    allowed_people = {item.get("id") for item in metadata_for(session_id).get("participants", [])}
    if participant and participant not in allowed_people:
        raise ValueError(f"Participante desconocido: {participant}")
    if speaker and speaker not in allowed_people:
        raise ValueError(f"Hablante desconocido: {speaker}")

    attributes = event.get("attributes") or {}
    if not isinstance(attributes, dict):
        raise ValueError("attributes debe ser un objeto")
    attribute_schema = definition.get("attributes") or {}
    clean_attributes = {}
    for name, value in attributes.items():
        if name not in attribute_schema:
            raise ValueError(f"Atributo '{name}' no permitido para {event_type}")
        allowed = attribute_schema[name].get("values") or []
        if allowed and value not in allowed:
            raise ValueError(f"Valor '{value}' no permitido para {event_type}.{name}")
        clean_attributes[name] = value

    clean = {"start_seconds": start, "end_seconds": end, "type": event_type}
    if participant:
        clean["participant"] = participant
    if speaker:
        clean["speaker"] = speaker
    participants = event.get("participants") or []
    if participants:
        if not isinstance(participants, list) or any(p not in allowed_people for p in participants):
            raise ValueError("participants contiene identificadores inválidos")
        clean["participants"] = participants
    if clean_attributes:
        clean["attributes"] = clean_attributes
    notes = str(event.get("notes") or "").strip()
    if notes:
        clean["notes"] = notes
    clean["es_ejemplo"] = bool(event.get("es_ejemplo", False))
    return clean


class Handler(BaseHTTPRequestHandler):
    server_version = "DEMUCAAnnotator/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args) -> None:
        print(f"[HTTP] {self.address_string()} - {format % args}")

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def error_json(self, error: Exception, status: int = 400) -> None:
        self.send_json({"error": str(error)}, status)

    def query(self) -> dict[str, str]:
        parsed = urlparse(self.path)
        return {key: values[0] for key, values in parse_qs(parsed.query).items() if values}

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("Solicitud demasiado grande")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/config":
                sessions = []
                for path in sorted(SESSIONS_DIR.iterdir()):
                    if not path.is_dir() or not SESSION_RE.fullmatch(path.name):
                        continue
                    try:
                        metadata = metadata_for(path.name)
                        video_for(path.name)
                    except (ValueError, OSError, json.JSONDecodeError):
                        continue
                    sessions.append({
                        "session_id": path.name,
                        "participants": metadata.get("participants", []),
                        "duration_seconds": metadata.get("technical", {}).get("duration_seconds"),
                    })
                return self.send_json({"sessions": sessions, "schema": public_schema()})
            if parsed.path == "/api/events":
                query = self.query()
                return self.send_json(read_events(query["session"], query["modality"]))
            if parsed.path == "/api/review-tasks":
                return self.send_json({"tasks": read_review_tasks(self.query()["session"])})
            if parsed.path == "/api/review-candidates":
                query = self.query()
                return self.send_json(read_review_candidates(query["session"], query["task"]))
            if parsed.path == "/api/pose":
                return self.send_json(read_pose_landmarks(self.query()["session"]))
            if parsed.path == "/media":
                return self.send_media(preview_video_for(self.query()["session"]))
            if parsed.path in ("/", "/index.html"):
                return self.send_static("index.html")
            if parsed.path == "/favicon.ico":
                self.send_response(HTTPStatus.NO_CONTENT)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if parsed.path.startswith("/static/"):
                return self.send_static(parsed.path.removeprefix("/static/"))
            self.send_error(HTTPStatus.NOT_FOUND)
        except (BrokenPipeError, ConnectionResetError):
            # El elemento <video> cancela rangos anteriores al buscar otra posición.
            # Es una desconexión normal del cliente, no un error del dataset.
            return
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            self.error_json(error, 400)

    def do_POST(self) -> None:
        endpoint = urlparse(self.path).path
        if endpoint == "/api/events/batch":
            try:
                body = self.read_body()
                session_id = body["session_id"]
                incoming = body["events"]
                if not isinstance(incoming, dict) or not incoming:
                    raise ValueError("Selecciona al menos una modalidad")
                unknown = set(incoming) - set(MODALITY_TO_SCHEMA)
                if unknown:
                    raise ValueError(f"Modalidades inválidas: {', '.join(sorted(unknown))}")
                # Validar el lote completo antes de escribir cualquier archivo.
                validated = {
                    modality: validate_event(session_id, modality, event)
                    for modality, event in incoming.items()
                }
                results = {}
                for modality, event in validated.items():
                    data = read_events(session_id, modality)
                    data["events"].append(event)
                    data["events"].sort(key=lambda item: (item["start_seconds"], item["end_seconds"]))
                    write_events(session_id, modality, data)
                    results[modality] = data["events"]
                return self.send_json({"events": results}, 201)
            except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
                return self.error_json(error, 400)
        if endpoint != "/api/events":
            return self.send_error(HTTPStatus.NOT_FOUND)
        try:
            body = self.read_body()
            session_id = body["session_id"]
            modality = body["modality"]
            event = validate_event(session_id, modality, body["event"])
            data = read_events(session_id, modality)
            data["events"].append(event)
            data["events"].sort(key=lambda item: (item["start_seconds"], item["end_seconds"]))
            write_events(session_id, modality, data)
            self.send_json(data, 201)
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            self.error_json(error, 400)

    def do_PUT(self) -> None:
        if urlparse(self.path).path != "/api/events":
            return self.send_error(HTTPStatus.NOT_FOUND)
        try:
            body = self.read_body()
            session_id = body["session_id"]
            modality = body["modality"]
            index = int(body["index"])
            event = validate_event(session_id, modality, body["event"])
            data = read_events(session_id, modality)
            if index < 0 or index >= len(data["events"]):
                raise ValueError("Índice de evento inválido")
            data["events"][index] = event
            data["events"].sort(key=lambda item: (item["start_seconds"], item["end_seconds"]))
            write_events(session_id, modality, data)
            self.send_json(data)
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            self.error_json(error, 400)

    def do_DELETE(self) -> None:
        if urlparse(self.path).path != "/api/events":
            return self.send_error(HTTPStatus.NOT_FOUND)
        try:
            query = self.query()
            session_id, modality, index = query["session"], query["modality"], int(query["index"])
            data = read_events(session_id, modality)
            if index < 0 or index >= len(data["events"]):
                raise ValueError("Índice de evento inválido")
            data["events"].pop(index)
            write_events(session_id, modality, data)
            self.send_json(data)
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            self.error_json(error, 400)

    def send_static(self, name: str) -> None:
        target = (STATIC_DIR / name).resolve()
        if STATIC_DIR.resolve() not in target.parents or not target.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND)
        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_media(self, path: Path) -> None:
        size = path.stat().st_size
        start, end = 0, size - 1
        range_header = self.headers.get("Range")
        status = HTTPStatus.OK
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if not match:
                return self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            if not match.group(1) and match.group(2):
                # Rango sufijo: los últimos N bytes (bytes=-N).
                suffix_length = min(int(match.group(2)), size)
                start, end = size - suffix_length, size - 1
            elif match.group(1):
                start = int(match.group(1))
                if match.group(2):
                    end = int(match.group(2))
            end = min(end, size - 1)
            if start > end or start >= size:
                return self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            status = HTTPStatus.PARTIAL_CONTENT
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with path.open("rb") as file:
            file.seek(start)
            remaining = length
            while remaining:
                chunk = file.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    # El navegador abrió otro rango y ya no necesita este flujo.
                    break
                remaining -= len(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Anotador audiovisual local DEMUCA")
    parser.add_argument("--host", default="127.0.0.1", help="Host local (predeterminado: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Puerto (predeterminado: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="No abrir el navegador automáticamente")
    args = parser.parse_args()
    if not STATIC_DIR.is_dir():
        parser.exit(1, f"[ERROR] No existe la interfaz: {STATIC_DIR}\n")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"[OK] Anotador disponible en {url}")
    print("Presiona Ctrl+C para detenerlo.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OK] Anotador detenido")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
