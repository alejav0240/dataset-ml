#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


def extraer_frames(raiz: Path, session_id: str, sobrescribir: bool) -> None:
    sesion = raiz / "dataset" / "sessions" / session_id
    video = sesion / "processed" / "video" / f"{session_id}_1280x720_10fps.mp4"
    salida = sesion / "processed" / "frames"

    if not video.is_file():
        print(f"No existe el video procesado: {video}", file=sys.stderr)
        raise SystemExit(1)

    salida.mkdir(parents=True, exist_ok=True)
    patron = salida / f"{session_id}_%06d.jpg"
    comando = [
        "ffmpeg",
        "-y" if sobrescribir else "-n",
        "-i",
        str(video),
        "-vf",
        "fps=1",
        "-q:v",
        "3",
        str(patron),
    ]

    print("Ejecutando:", " ".join(comando))
    try:
        subprocess.run(comando, check=True)
    except subprocess.CalledProcessError as error:
        print(f"Error al extraer frames: {error}", file=sys.stderr)
        raise SystemExit(error.returncode) from error

    frames = sorted(salida.glob(f"{session_id}_*.jpg"))
    print(f"Frames extraídos: {len(frames)}")
    print(f"Directorio: {salida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extrae un frame por segundo del video procesado."
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
        help="Regenerar los frames existentes",
    )
    args = parser.parse_args()
    extraer_frames(args.raiz, args.session_id, args.sobrescribir)
