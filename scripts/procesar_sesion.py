#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path


FPS_OBJETIVO = 10
ANCHO_OBJETIVO = 1280
ALTO_OBJETIVO = 720
MUESTREO_AUDIO = 16000
CANALES_AUDIO = 1


def ejecutar(comando: list[str]) -> None:
    print("Ejecutando:", " ".join(comando))
    try:
        subprocess.run(comando, check=True)
    except subprocess.CalledProcessError as error:
        print(f"Error durante el procesamiento: {error}", file=sys.stderr)
        raise SystemExit(error.returncode) from error


def cargar_metadata(ruta: Path) -> dict:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"Metadata JSON inválida: {ruta}: {error}", file=sys.stderr)
        raise SystemExit(1) from error


def guardar_metadata(ruta: Path, metadata: dict) -> None:
    ruta.write_text(
        json.dumps(metadata, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def procesar_sesion(raiz: Path, session_id: str, sobrescribir: bool) -> None:
    sesion = raiz / "dataset" / "sessions" / session_id
    metadata_path = sesion / "metadata" / "session.json"
    metadata = cargar_metadata(metadata_path)

    video_original = sesion / metadata["recording"]["original_video"]
    audio_procesado = sesion / "processed" / "audio" / f"{session_id}_16khz_mono.wav"
    video_procesado = sesion / "processed" / "video" / f"{session_id}_1280x720_10fps.mp4"

    if not video_original.is_file():
        print(f"No existe el video original: {video_original}", file=sys.stderr)
        raise SystemExit(1)

    audio_procesado.parent.mkdir(parents=True, exist_ok=True)
    video_procesado.parent.mkdir(parents=True, exist_ok=True)

    if sobrescribir or not video_procesado.exists():
        ejecutar([
            "ffmpeg", "-y" if sobrescribir else "-n",
            "-i", str(video_original),
            "-vf", f"scale={ANCHO_OBJETIVO}:{ALTO_OBJETIVO}:force_original_aspect_ratio=decrease,pad={ANCHO_OBJETIVO}:{ALTO_OBJETIVO}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(FPS_OBJETIVO),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            # Mantener una pista AAC en el MP4 para reproducción y anotación.
            # El WAV mono se genera además como entrada independiente del pipeline.
            "-c:a", "aac",
            "-b:a", "128k",
            "-ac", str(CANALES_AUDIO),
            "-ar", str(MUESTREO_AUDIO),
            "-shortest",
            str(video_procesado),
        ])

    if sobrescribir or not audio_procesado.exists():
        ejecutar([
            "ffmpeg", "-y" if sobrescribir else "-n",
            "-i", str(video_original),
            "-vn",
            "-ac", str(CANALES_AUDIO),
            "-ar", str(MUESTREO_AUDIO),
            "-c:a", "pcm_s16le",
            str(audio_procesado),
        ])

    metadata.setdefault("processing", {})["video_processed"] = True
    metadata["processing"]["audio_processed"] = True
    guardar_metadata(metadata_path, metadata)
    print(f"Procesamiento completado para {session_id}")
    print(f"Video: {video_procesado}")
    print(f"Audio: {audio_procesado}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normaliza el video y el audio de una sesión del dataset DEMUCA."
    )
    parser.add_argument("session_id", help="Identificador de sesión, por ejemplo S001")
    parser.add_argument(
        "--raiz",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Directorio raíz de dataset",
    )
    parser.add_argument(
        "--sobrescribir",
        action="store_true",
        help="Regenerar los archivos procesados existentes",
    )
    args = parser.parse_args()
    procesar_sesion(args.raiz, args.session_id, args.sobrescribir)


if __name__ == "__main__":
    main()
