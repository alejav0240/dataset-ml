#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

def separar_video_y_audio(video_input: Path, dir_video: Path, dir_audio: Path):
    # Crear los directorios de destino si no existen
    dir_video.mkdir(parents=True, exist_ok=True)
    dir_audio.mkdir(parents=True, exist_ok=True)

    # Definir nombres de salida manteniendo el nombre original del archivo
    nombre_base = video_input.stem
    salida_video = dir_video / f"{nombre_base}_solo_video.mp4"
    salida_audio = dir_audio / f"{nombre_base}_audio.mp3"

    print(f"Procesando: {video_input.name}")
    print("=" * 40)

    # 1. Extraer solo la pista de video (descartar audio con -an)
    cmd_video = [
        "ffmpeg", "-y",
        "-i", str(video_input),
        "-c:v", "copy",
        "-an",
        str(salida_video)
    ]

    # 2. Extraer solo la pista de audio a MP3
    cmd_audio = [
        "ffmpeg", "-y",
        "-i", str(video_input),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",  # Calidad alta (VBR ~190-250 kbps)
        str(salida_audio)
    ]

    try:
        print(f"Extrayendo video a: {salida_video}")
        subprocess.run(cmd_video, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        print(f"Extrayendo audio a: {salida_audio}")
        subprocess.run(cmd_audio, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        print("=" * 40)
        print("¡Proceso completado exitosamente!")

    except subprocess.CalledProcessError as e:
        print(f"\nError durante la ejecución de FFmpeg:\n{e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Extrae y separa el video (sin audio) y el sonido de un archivo .mp4."
    )
    
    # Definición de parámetros
    parser.add_argument(
        "-i", "--input",
        required=True,
        type=Path,
        help="Ruta del archivo .mp4 de origen."
    )
    parser.add_argument(
        "-dv", "--dir-video",
        required=True,
        type=Path,
        help="Directorio donde se guardará el archivo de video sin audio."
    )
    parser.add_argument(
        "-da", "--dir-audio",
        required=True,
        type=Path,
        help="Directorio donde se guardará el archivo de audio."
    )

    args = parser.parse_args()

    # Validaciones previas
    if not args.input.is_file():
        print(f"Error: El archivo de entrada '{args.input}' no existe.", file=sys.stderr)
        sys.exit(1)

    separar_video_y_audio(args.input, args.dir_video, args.dir_audio)

if __name__ == "__main__":
    main()
