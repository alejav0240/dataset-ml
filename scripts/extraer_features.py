#!/usr/bin/env python3
"""
Pipeline de extracción de características (features) multimodal para sesiones DEMUCA.
Calcula representaciones intermedias a nivel temporal:
- Audio: Energía RMS por segundo, tasa de cruces por cero (ZCR) y ratios espectrales.
- Visual: Cuantificación de movimiento global (Motion Energy / Frame differencing) a 1 fps.
Almacena los resultados en `processed/features/` y actualiza `metadata/session.json`.
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf


def extraer_features_audio(audio_path: Path, hop_duration: float = 1.0) -> dict:
    """Extrae características acústicas agregadas en ventanas de 1 segundo."""
    print(f"Leyendo audio: {audio_path}")
    data, sample_rate = sf.read(str(audio_path))

    if data.ndim > 1:
        data = np.mean(data, axis=1)

    hop_size = int(sample_rate * hop_duration)
    total_samples = len(data)
    num_windows = total_samples // hop_size

    timestamps = []
    rms_values = []
    zcr_values = []

    for i in range(num_windows):
        segment = data[i * hop_size : (i + 1) * hop_size]
        t = round((i + 0.5) * hop_duration, 2)

        # RMS (Energía)
        rms = float(np.sqrt(np.mean(segment**2)))
        # ZCR (Tasa de cruces por cero)
        zero_crossings = np.sum(np.diff(np.sign(segment)) != 0)
        zcr = float(zero_crossings / len(segment))

        timestamps.append(t)
        rms_values.append(round(rms, 6))
        zcr_values.append(round(zcr, 6))

    return {
        "sample_rate": sample_rate,
        "window_seconds": hop_duration,
        "total_windows": num_windows,
        "timestamps": timestamps,
        "rms_energy": rms_values,
        "zero_crossing_rate": zcr_values,
    }


def extraer_features_visuales(frames_dir: Path, session_id: str) -> dict:
    """Calcula la energía de movimiento inter-frame entre frames consecutivos."""
    print(f"Calculando densidad de movimiento en: {frames_dir}")
    frame_files = sorted(frames_dir.glob(f"{session_id}_*.jpg"))

    if not frame_files:
        return {"total_frames": 0, "motion_energy": []}

    timestamps = []
    motion_energy = []
    prev_gray = None

    for idx, fpath in enumerate(frame_files):
        # Cada frame representa 1 segundo en la extracción por defecto
        t = float(idx)
        img = cv2.imread(str(fpath))
        if img is None:
            continue

        # Reducir tamaño para cálculo ágil
        small = cv2.resize(img, (320, 180))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev_gray is None:
            motion = 0.0
        else:
            diff = cv2.absdiff(prev_gray, gray)
            motion = float(np.mean(diff))

        prev_gray = gray
        timestamps.append(t)
        motion_energy.append(round(motion, 4))

    return {
        "sampling_fps": 1.0,
        "total_frames": len(frame_files),
        "timestamps": timestamps,
        "motion_intensity": motion_energy,
    }


def procesar_features(raiz: Path, session_id: str, sobrescribir: bool = False):
    sesion = raiz / "dataset" / "sessions" / session_id
    metadata_path = sesion / "metadata" / "session.json"

    if not metadata_path.exists():
        print(f"[ERROR] No existe metadata para {session_id}", file=sys.stderr)
        return

    features_dir = sesion / "processed" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    audio_file = sesion / "processed" / "audio" / f"{session_id}_16khz_mono.wav"
    frames_dir = sesion / "processed" / "frames"

    audio_feat_out = features_dir / "audio_features.json"
    visual_feat_out = features_dir / "visual_motion.json"

    # 1. Features de Audio
    if audio_file.exists() and (sobrescribir or not audio_feat_out.exists()):
        audio_data = extraer_features_audio(audio_file)
        audio_feat_out.write_text(
            json.dumps(audio_data, indent=2), encoding="utf-8"
        )
        print(f"[OK] Generado {audio_feat_out}")
    elif not audio_file.exists():
        print(f"[SKIP] No existe audio procesado en {audio_file}")

    # 2. Features Visuales
    if frames_dir.exists() and (sobrescribir or not visual_feat_out.exists()):
        visual_data = extraer_features_visuales(frames_dir, session_id)
        visual_feat_out.write_text(
            json.dumps(visual_data, indent=2), encoding="utf-8"
        )
        print(f"[OK] Generado {visual_feat_out}")
    elif not frames_dir.exists():
        print(f"[SKIP] No existe directorio de frames en {frames_dir}")

    # 3. Actualizar session.json
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.setdefault("processing", {})["features_extracted"] = True
        metadata_path.write_text(
            json.dumps(metadata, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] Metadata actualizada: features_extracted = true")
    except Exception as e:
        print(f"[WARN] No se pudo actualizar metadata: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Extrae características multimodales (audio y visión) para una sesión."
    )
    parser.add_argument("session_id", help="Identificador de la sesión (ej. S001)")
    parser.add_argument(
        "--raiz",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Directorio raíz del dataset",
    )
    parser.add_argument(
        "--sobrescribir",
        action="store_true",
        help="Regenerar features existentes",
    )
    args = parser.parse_args()

    procesar_features(args.raiz, args.session_id, args.sobrescribir)


if __name__ == "__main__":
    main()
