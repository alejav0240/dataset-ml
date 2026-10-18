#!/usr/bin/env python3

from pathlib import Path
import argparse
import json
from datetime import datetime


def crear_estructura(base_dir: str, session_id: str):
    base = Path(base_dir)
    session_dir = base / "sessions" / session_id

    directories = [
        # Datos originales
        "raw/video",
        "raw/audio",

        # Datos procesados
        "processed/video",
        "processed/audio",
        "processed/frames",
        "processed/features",

        # Anotaciones
        "annotations/visual",
        "annotations/audio",
        "annotations/interaction",
        "annotations/demuca",

        # Metadata
        "metadata",
    ]

    for directory in directories:
        (session_dir / directory).mkdir(parents=True, exist_ok=True)

    # Metadata inicial
    metadata = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "patient_id": None,
        "therapist_id": None,
        "duration_seconds": None,
        "video": {
            "filename": None,
            "fps": None,
            "width": None,
            "height": None,
        },
        "audio": {
            "filename": None,
            "sample_rate": None,
            "channels": None,
        },
        "dataset_version": "0.1.0",
        "annotation_status": {
            "visual": "pendiente",
            "audio": "pendiente",
            "interaction": "pendiente",
            "demuca": "pendiente",
        },
    }

    metadata_path = session_dir / "metadata" / "session.json"

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    # README de la sesión
    readme = f"""# Sesión {session_id}

## Identificación

- ID de sesión: {session_id}
- Paciente: pendiente
- Terapeuta: pendiente

## Archivos originales

Colocar aquí:

- Video original en `raw/video/`
- Audio original en `raw/audio/`

## Procesamiento

Los archivos derivados se almacenan en:

- `processed/video/`
- `processed/audio/`
- `processed/frames/`
- `processed/features/`

## Anotaciones

### Visual

`annotations/visual/`

### Audio

`annotations/audio/`

### Interacción

`annotations/interaction/`

### DEMUCA

`annotations/demuca/`

## Estado

- [ ] Video cargado
- [ ] Audio extraído
- [ ] Video procesado
- [ ] Audio procesado
- [ ] Anotación visual
- [ ] Anotación audio
- [ ] Anotación interacción
- [ ] Evaluación DEMUCA
- [ ] Revisión
"""

    readme_path = session_dir / "README.md"
    readme_path.write_text(readme, encoding="utf-8")

    print(f"\nSesión creada correctamente:")
    print(f"  {session_dir}")
    print(f"\nMetadata:")
    print(f"  {metadata_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Crea la estructura de una sesión del dataset multimodal."
    )

    parser.add_argument(
        "session_id",
        help="Identificador de la sesión. Ejemplo: S001"
    )

    parser.add_argument(
        "--output",
        default="./dataset",
        help="Directorio raíz del dataset."
    )

    args = parser.parse_args()

    crear_estructura(
        base_dir=args.output,
        session_id=args.session_id,
    )


if __name__ == "__main__":
    main()
