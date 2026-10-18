#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


# ============================================================
# Utilidades
# ============================================================

def escribir_texto(path: Path, contenido: str, force: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not force:
        print(f"[SKIP] {path}")
        return

    path.write_text(contenido.strip() + "\n", encoding="utf-8")
    print(f"[CREATE] {path}")


def escribir_json(path: Path, data: dict, force: bool = False):
    contenido = json.dumps(
        data,
        indent=2,
        ensure_ascii=False
    )

    escribir_texto(path, contenido, force)


def crear_directorio(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    print(f"[DIR]    {path}")


# ============================================================
# Configuración
# ============================================================

DATASET_YAML = """
dataset:
  name: "Dataset multimodal de musicoterapia DEMUCA"
  version: "0.1.0"

  modalities:
    - video
    - audio
    - interaccion
    - clinica

  temporal:
    primary_unit: event
    processing_window_seconds: 5
    context_window_seconds: 30

participants:
  allowed:
    - PACIENTE
    - TERAPEUTA
    - OTRO
    - DESCONOCIDO

events:
  visual:
    - MOVIMIENTO
    - MOVIMIENTO_REPETITIVO
    - CONTACTO_VISUAL
    - INTERACCION_OBJETO
    - ORIENTACION_CORPORAL

  audio:
    - VOCALIZACION
    - HABLA
    - RISA
    - LLANTO
    - GRITO
    - SILENCIO
    - ACTIVIDAD_MUSICAL

  interaction:
    - MIRADA
    - GESTO
    - TACTO
    - IMITACION
    - RESPUESTA
    - ACTIVIDAD_CONJUNTA
    - INTERACCION_MUSICAL
    - INTERACCION_VERBAL

processing:
  video:
    target_fps: 10
    width: 1280
    height: 720

  audio:
    sample_rate: 16000
    channels: 1

storage:
  raw: "raw"
  processed: "processed"
  annotations: "annotations"
  metadata: "metadata"
"""


ANNOTATION_SCHEMA_YAML = """
  visual:

  MOVIMIENTO:
    description: "Movimiento corporal observable"
    participant_required: true

    attributes:

      intensidad:
        type: categorical
        values:
          - LOW
          - MEDIUM
          - HIGH

      parte_cuerpo:
        type: categorical
        values:
          - HEAD
          - ARM
          - HAND
          - TORSO
          - LEG
          - WHOLE_BODY
          - OTRO


  MOVIMIENTO_REPETITIVO:
    description: "Movimiento corporal repetitivo observable"
    participant_required: true

    attributes:

      tipo:
        type: categorical
        values:
          - HAND
          - ARM
          - HEAD
          - BODY
          - OTRO

      frecuencia:
        type: categorical
        values:
          - LOW
          - MEDIUM
          - HIGH


  CONTACTO_VISUAL:
    description: "Orientación visual hacia otra persona u objetivo"
    participant_required: true

    attributes:

      objetivo:
        type: categorical
        values:
          - PACIENTE
          - TERAPEUTA
          - OBJECT
          - CAMERA
          - OTRO


  INTERACCION_OBJETO:
    description: "Interacción física con un objeto"
    participant_required: true

    attributes:

      accion:
        type: categorical
        values:
          - TOCAR
          - AGARRAR
          - SOSTENER
          - MOVER
          - USAR
          - SOLTAR

      tipo_objeto:
        type: categorical
        values:
          - DRUM
          - GUITAR
          - PIANO
          - MARACA
          - TOY
          - OTRO


audio:

  VOCALIZACION:
    description: "Producción vocal observable del participante"
    speaker_required: true

    attributes:

      tipo:
        type: categorical
        values:
          - VOCALIZACION
          - BALBUCEO
          - HABLA
          - OTRO


  RISA:
    description: "Risa observable"


  LLANTO:
    description: "Llanto observable"


  GRITO:
    description: "Grito o vocalización de alta intensidad"


  SILENCIO:
    description: "Ausencia de actividad vocal"


  ACTIVIDAD_MUSICAL:
    description: "Actividad musical observable"

    attributes:

      tipo:
        type: categorical
        values:
          - TERAPEUTA_TOCANDO
          - PACIENTE_TOCANDO
          - TOCANDO_JUNTOS
          - MUSICA_GRABADA
          - CANTO
          - ACTIVIDAD_RITMICA


interaccion:

  RESPUESTA:
    description: "Respuesta del paciente a una acción del terapeuta"

  IMITACION:
    description: "Imitación observable"

  MIRADA:
    description: "Interacción mediante orientación visual"

  GESTO:
    description: "Interacción mediante gesto"

  TACTO:
    description: "Contacto físico"

  ACTIVIDAD_CONJUNTA:
    description: "Actividad compartida"

  INTERACCION_MUSICAL:
    description: "Interacción mediante actividad musical"

  INTERACCION_VERBAL:
    description: "Interacción verbal"
"""


REQUIREMENTS = """
PyYAML>=6.0
jsonschema>=4.23
pydantic>=2.8
"""


PROJECT_README = """
# Dataset multimodal de musicoterapia DEMUCA

Dataset multimodal para investigación sobre evaluación asistida
por inteligencia artificial de sesiones de musicoterapia.

## Modalidades

- Video
- Audio
- Interacción
- Evaluación clínica DEMUCA

## Principio fundamental

Las observaciones audiovisuales se almacenan independientemente
de la evaluación clínica.

El sistema debe aprender posteriormente la relación:

Observación → Evidencia → Evaluación DEMUCA

## Estructura

```text
dataset/
└── sessions/
    └── S001/
        ├── metadata/
        ├── raw/
        ├── processed/
        └── annotations/

```

## Versionado

Versión inicial:

0.1.0

## Estado

Dataset en fase de construcción y validación.
"""

SESSION_README = """

# Sesión S001

## Información

* ID de sesión: S001
* Versión del conjunto de datos: 0.1.0
* Paciente: P001
* Terapeuta: T001

## Estado

| Proceso | Estado |
| --- | --- |
| Media separada | Pendiente |
| Audio normalizado | Pendiente |
| Video normalizado | Pendiente |
| Frames | Pendiente |
| Features visuales | Pendiente |
| Features de audio | Pendiente |
| Anotación visual | Pendiente |
| Anotación audio | Pendiente |
| Anotación interacción | Pendiente |
| Evaluación DEMUCA | Pendiente |

## Observaciones

Pendiente de revisión.

## Calidad

### Video

Pendiente.

### Audio

Pendiente.

### Oclusiones

Pendiente.
"""

SESSION_SCHEMA = {
"$schema": "https://json-schema.org/draft/2020-12/schema",
"title": "Sesión de musicoterapia",
"type": "object",
"required": [
"session_id",
"dataset_version",
"participants",
"recording"
],
"properties": {
"session_id": {
"type": "string",
"pattern": "^S[0-9]{3,}$"
},
"dataset_version": {
"type": "string"
},
"participants": {
"type": "array",
"minItems": 1,
"items": {
"type": "object",
"required": [
"id",
"role"
],
"properties": {
"id": {
"type": "string"
},
"role": {
"type": "string",
"enum": [
"PACIENTE",
"TERAPEUTA",
"OTRO",
"DESCONOCIDO"
]
}
}
}
},
"recording": {
"type": "object",
"required": [
"original_video"
],
"properties": {
"original_video": {
"type": "string"
},
"audio": {
"type": "string"
},
"video_only": {
"type": "string"
}
}
}
}
}

# ============================================================

# Creación de estructura

# ============================================================

def crear_estructura_sesion(session_id: str):
  session = ROOT / "dataset" / "sessions" / session_id

  directories = [
    session / "metadata",
    session / "raw" / "original",
    session / "raw" / "video",
    session / "raw" / "audio",
    session / "processed" / "video",
    session / "processed" / "audio",
    session / "processed" / "frames",
    session / "processed" / "features",
    session / "annotations" / "visual",
    session / "annotations" / "audio",
    session / "annotations" / "interaction",
    session / "annotations" / "demuca",
  ]

  for directory in directories:
    crear_directorio(directory)

# --------------------------------------------------------
# Metadata
# --------------------------------------------------------

  metadata = {
    "session_id": session_id,
    "dataset_version": "0.1.0",
    "participants": [
        {
            "id": "P001",
            "role": "PACIENTE"
        },
        {
            "id": "T001",
            "role": "TERAPEUTA"
        }
    ],
    "recording": {
        "original_video": "raw/original/",
        "audio": "raw/audio/",
        "video_only": "raw/video/"
    },
    "technical": {
        "duration_seconds": None,
        "video_fps": None,
        "video_width": None,
        "video_height": None,
        "audio_sample_rate": None,
        "audio_channels": None
    },
    "processing": {
        "video_processed": False,
        "audio_processed": False,
        "frames_extracted": False,
        "features_extracted": False
    },
    "annotation": {
        "visual": False,
        "audio": False,
        "interaction": False,
        "demuca": False
    },
    "quality": {
        "video_quality": None,
        "audio_quality": None,
        "occlusion": None,
        "background_noise": None
    }
  }

  escribir_json(session / "metadata" / "session.json", metadata)

# --------------------------------------------------------
# Anotaciones
# --------------------------------------------------------

  annotations = {
    "visual": {
        "session_id": session_id,
        "events": []
    },
    "audio": {
        "session_id": session_id,
        "events": []
    },
    "interaction": {
        "session_id": session_id,
        "events": []
    },
    "demuca": {
        "session_id": session_id,
        "evaluations": []
    }
  }

  for annotation_type in ("visual", "audio", "interaction"):
    escribir_json(
      session / "annotations" / annotation_type / "events.json",
      annotations[annotation_type],
    )
  escribir_json(
    session / "annotations" / "demuca" / "evaluations.json",
    annotations["demuca"],
  )

# --------------------------------------------------------
# README
# --------------------------------------------------------

  escribir_texto(
    session / "README.md",
    SESSION_README.replace("Sesión S001", f"Sesión {session_id}")
      .replace("ID de sesión: S001", f"ID de sesión: {session_id}"),
  )

def crear_archivos_globales():
  crear_directorio(ROOT / "config")
  crear_directorio(ROOT / "schemas")
  crear_directorio(ROOT / "scripts")

  escribir_texto(ROOT / "config" / "dataset.yaml", DATASET_YAML)
  escribir_texto(
    ROOT / "config" / "annotation_schema.yaml",
    ANNOTATION_SCHEMA_YAML,
  )
  escribir_json(ROOT / "schemas" / "session.schema.json", SESSION_SCHEMA)
  escribir_texto(ROOT / "requirements.txt", REQUIREMENTS)
  escribir_texto(ROOT / "README.md", PROJECT_README)

# ============================================================

# Validador

# ============================================================

VALIDADOR = r'''#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from jsonschema import validate
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset" / "sessions"
SCHEMA_FILE = ROOT / "schemas" / "session.schema.json"


def cargar_json(path: Path):
  with path.open("r", encoding="utf-8") as file:
    return json.load(file)


def validar_sesion(session_dir: Path, schema: dict) -> bool:
  session_id = session_dir.name
  metadata_file = session_dir / "metadata" / "session.json"

  if not metadata_file.exists():
    print(f"[ERROR] {session_id}: falta metadata/session.json")
    return False

  try:
    validate(instance=cargar_json(metadata_file), schema=schema)
  except ValidationError as error:
    print(f"[ERROR] {session_id}: metadata inválida")
    print(f"        {error.message}")
    return False
  except json.JSONDecodeError as error:
    print(f"[ERROR] {session_id}: JSON inválido")
    print(f"        {error}")
    return False

  print(f"[OK] {session_id}")
  return True


def main():
  if not DATASET_DIR.exists():
    print(f"[ERROR] No existe: {DATASET_DIR}")
    sys.exit(1)

  schema = cargar_json(SCHEMA_FILE)
  sessions = sorted(path for path in DATASET_DIR.iterdir() if path.is_dir())

  if not sessions:
    print("[WARNING] No existen sesiones")
    return

  validas = sum(validar_sesion(session, schema) for session in sessions)
  print("\n" + "=" * 40)
  print("VALIDACIÓN DEL DATASET")
  print("=" * 40)
  print(f"Sesiones:  {len(sessions)}")
  print(f"Válidas:   {validas}")
  print(f"Inválidas: {len(sessions) - validas}")


if __name__ == "__main__":
  main()
'''

# ============================================================

# Main

# ============================================================

def main():
  parser = argparse.ArgumentParser(
    description="Crea la estructura del dataset multimodal DEMUCA"
  )
  parser.add_argument(
    "--session",
    default="S001",
    help="ID de la sesión a crear",
  )
  parser.add_argument(
    "--force",
    action="store_true",
    help="Sobrescribir archivos existentes",
  )
  args = parser.parse_args()

  print("\n" + "=" * 60)
  print(" DEMUCA MULTIMODAL DATASET")
  print("=" * 60 + "\n")

  crear_archivos_globales()
  crear_estructura_sesion(args.session)

  validador_path = ROOT / "scripts" / "validar_dataset.py"
  escribir_texto(validador_path, VALIDADOR, args.force)

  print("\n" + "=" * 60)
  print(" ESTRUCTURA CREADA")
  print("=" * 60)
  print(f"\nSesión: {args.session}")
  print("\nSiguiente paso:")
  print("\n  1. Coloca el video original en:")
  print(f"     dataset/sessions/{args.session}/raw/original/")
  print("\n  2. Coloca el audio en:")
  print(f"     dataset/sessions/{args.session}/raw/audio/")
  print("\n  3. Ejecuta:")
  print("     python scripts/validar_dataset.py\n")


if __name__ == "__main__":
  main()

