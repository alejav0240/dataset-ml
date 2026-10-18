#!/usr/bin/env python3
"""Genera cuadernos EDA reproducibles para cada sesion y para el dataset."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_DIR = ROOT / "dataset" / "sessions"


def cell(cell_type: str, source: str) -> dict:
    return {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source.strip().splitlines()],
        **({"execution_count": None, "outputs": []} if cell_type == "code" else {}),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def individual_notebook(session_id: str) -> dict:
    return notebook([
        cell("markdown", f"""
# EDA de la sesion {session_id}

Analisis descriptivo de los metadatos, anotaciones DEMUCA, eventos y features disponibles.
Los valores muestran disponibilidad de datos; no constituyen evaluacion clinica ni ground truth.
"""),
        cell("code", """
from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd

plt.style.use('seaborn-v0_8-whitegrid')
SESSION_ID = '""" + session_id + """'

def find_dataset_root():
    for base in (Path.cwd(), *Path.cwd().parents):
        for candidate in (base, base / 'dataset'):
            if (candidate / 'sessions').is_dir():
                return candidate
    raise FileNotFoundError('No se encontro la raiz del dataset. Abre Jupyter desde el directorio dataset.')

def load_json(path, default):
    if not path.exists():
        return default
    with path.open(encoding='utf-8') as file:
        return json.load(file)

DATASET_ROOT = find_dataset_root()
SESSION_DIR = DATASET_ROOT / 'sessions' / SESSION_ID
ANNOTATIONS = SESSION_DIR / 'annotations'
metadata = load_json(SESSION_DIR / 'metadata' / 'session.json', {})
print(f'Sesion: {SESSION_ID}')
print(f'Directorio: {SESSION_DIR}')
"""),
        cell("markdown", """
## 1. Cobertura y procesamiento
"""),
        cell("code", """
processing = metadata.get('processing', {})
annotation_status = metadata.get('annotation', {})
technical = metadata.get('technical', {})

coverage = pd.DataFrame([
    {'Indicador': 'Duracion (s)', 'Valor': technical.get('duration_seconds')},
    {'Indicador': 'Video procesado', 'Valor': processing.get('video_processed', False)},
    {'Indicador': 'Audio procesado', 'Valor': processing.get('audio_processed', False)},
    {'Indicador': 'Frames extraidos', 'Valor': processing.get('frames_extracted', False)},
    {'Indicador': 'Features extraidas', 'Valor': processing.get('features_extracted', False)},
    {'Indicador': 'Anotacion visual', 'Valor': annotation_status.get('visual', False)},
    {'Indicador': 'Anotacion audio', 'Valor': annotation_status.get('audio', False)},
    {'Indicador': 'Anotacion interaccion', 'Valor': annotation_status.get('interaction', False)},
    {'Indicador': 'Evaluacion DEMUCA', 'Valor': annotation_status.get('demuca', False)},
])
display(coverage)
"""),
        cell("markdown", """
## 2. Eventos anotados
"""),
        cell("code", """
modalities = ('visual', 'audio', 'interaction')
event_sources = {
    modality: load_json(ANNOTATIONS / modality / 'events.json', {'events': []}).get('events', [])
    for modality in modalities
}
event_counts = pd.DataFrame([
    {'Modalidad': modality.title(), 'Eventos': len(events)}
    for modality, events in event_sources.items()
])
display(event_counts)

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(event_counts['Modalidad'], event_counts['Eventos'], color=['#2563eb', '#f59e0b', '#0891b2'])
ax.set(title=f'Eventos anotados: {SESSION_ID}', ylabel='Numero de eventos')
plt.tight_layout()
plt.show()

events = pd.DataFrame([
    {'modalidad': modality, **event}
    for modality, source_events in event_sources.items()
    for event in source_events
])
if events.empty:
    print('No hay eventos anotados para esta sesion.')
else:
    display(events.groupby(['modalidad', 'type']).size().rename('eventos').reset_index())
"""),
        cell("markdown", """
## 3. Evaluacion DEMUCA
"""),
        cell("code", """
demuca = load_json(ANNOTATIONS / 'demuca' / 'evaluations.json', {'evaluations': []})
evaluations = demuca.get('evaluations', [])
if not evaluations:
    print('No hay evaluaciones DEMUCA registradas para esta sesion.')
else:
    evaluation = evaluations[0]
    responses = pd.DataFrame(evaluation.get('responses', []))
    total = evaluation.get('total_score')
    maximum = evaluation.get('max_total_score')
    print(f'Puntaje DEMUCA: {total} / {maximum}')
    if not responses.empty:
        responses['score'] = pd.to_numeric(responses['score'])
        by_category = responses.groupby('category', as_index=False)['score'].mean().sort_values('score')
        display(by_category)
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh(by_category['category'], by_category['score'], color='#16a34a')
        ax.set(xlim=(0, 2), xlabel='Puntaje promedio (0-2)', title='Promedio DEMUCA por categoria')
        plt.tight_layout()
        plt.show()
"""),
        cell("markdown", """
## 4. Features disponibles
"""),
        cell("code", """
feature_files = {
    'Audio RMS': SESSION_DIR / 'processed' / 'features' / 'audio_features.json',
    'Movimiento visual': SESSION_DIR / 'processed' / 'features' / 'visual_motion.json',
}
available_features = pd.DataFrame([
    {'Feature': name, 'Disponible': path.exists()}
    for name, path in feature_files.items()
])
display(available_features)

audio_features = load_json(feature_files['Audio RMS'], {})
motion_features = load_json(feature_files['Movimiento visual'], {})
if audio_features.get('rms_energy'):
    plt.figure(figsize=(10, 3))
    plt.plot(audio_features.get('timestamps', []), audio_features['rms_energy'], linewidth=0.7, color='#f59e0b')
    plt.title('Energia RMS de audio')
    plt.xlabel('Tiempo (s)')
    plt.tight_layout()
    plt.show()
if motion_features.get('motion_intensity'):
    plt.figure(figsize=(10, 3))
    plt.plot(motion_features.get('timestamps', []), motion_features['motion_intensity'], linewidth=0.7, color='#2563eb')
    plt.title('Intensidad de movimiento visual')
    plt.xlabel('Tiempo (s)')
    plt.tight_layout()
    plt.show()
"""),
        cell("markdown", """
## 5. Conclusion

Este cuaderno resume unicamente los datos presentes en disco. Las sesiones sin medios,
features o anotaciones se mantienen en el analisis para hacer visible la cobertura real
del dataset, no como evidencia de ausencia de conducta.
"""),
    ])


def dataset_notebook() -> dict:
    return notebook([
        cell("markdown", """
# EDA general del dataset DEMUCA

Analisis de cobertura, procesamiento, anotaciones y evaluaciones DEMUCA de todas las
sesiones encontradas. Es un inventario descriptivo, no un analisis clinico ni de entrenamiento.
"""),
        cell("code", """
from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd

plt.style.use('seaborn-v0_8-whitegrid')

def find_dataset_root():
    for base in (Path.cwd(), *Path.cwd().parents):
        for candidate in (base, base / 'dataset'):
            if (candidate / 'sessions').is_dir():
                return candidate
    raise FileNotFoundError('No se encontro la raiz del dataset. Abre Jupyter desde el directorio dataset.')

def load_json(path, default):
    if not path.exists():
        return default
    with path.open(encoding='utf-8') as file:
        return json.load(file)

DATASET_ROOT = find_dataset_root()
SESSIONS_DIR = DATASET_ROOT / 'sessions'
session_dirs = sorted(path for path in SESSIONS_DIR.iterdir() if path.is_dir())
print(f'Sesiones encontradas: {len(session_dirs)}')
"""),
        cell("markdown", """
## 1. Inventario de sesiones
"""),
        cell("code", """
rows = []
all_events = []
all_responses = []
for session_dir in session_dirs:
    session_id = session_dir.name
    metadata = load_json(session_dir / 'metadata' / 'session.json', {})
    processing = metadata.get('processing', {})
    annotation = metadata.get('annotation', {})
    technical = metadata.get('technical', {})
    event_counts = {}
    for modality in ('visual', 'audio', 'interaction'):
        events = load_json(session_dir / 'annotations' / modality / 'events.json', {'events': []}).get('events', [])
        event_counts[modality] = len(events)
        all_events.extend({'session_id': session_id, 'modality': modality, **event} for event in events)
    evaluations = load_json(session_dir / 'annotations' / 'demuca' / 'evaluations.json', {'evaluations': []}).get('evaluations', [])
    responses = evaluations[0].get('responses', []) if evaluations else []
    all_responses.extend({'session_id': session_id, **response} for response in responses)
    rows.append({
        'session_id': session_id,
        'duration_seconds': technical.get('duration_seconds'),
        'video_processed': processing.get('video_processed', False),
        'audio_processed': processing.get('audio_processed', False),
        'features_extracted': processing.get('features_extracted', False),
        'visual_events': event_counts['visual'],
        'audio_events': event_counts['audio'],
        'interaction_events': event_counts['interaction'],
        'demuca_evaluations': len(evaluations),
        'demuca_total': evaluations[0].get('total_score') if evaluations else None,
        'demuca_max': evaluations[0].get('max_total_score') if evaluations else None,
    })

sessions = pd.DataFrame(rows)
display(sessions)
"""),
        cell("markdown", """
## 2. Cobertura del pipeline
"""),
        cell("code", """
coverage = pd.DataFrame([
    {'Etapa': 'Video procesado', 'Sesiones': sessions['video_processed'].sum()},
    {'Etapa': 'Audio procesado', 'Sesiones': sessions['audio_processed'].sum()},
    {'Etapa': 'Features extraidas', 'Sesiones': sessions['features_extracted'].sum()},
    {'Etapa': 'Con eventos', 'Sesiones': ((sessions[['visual_events', 'audio_events', 'interaction_events']].sum(axis=1)) > 0).sum()},
    {'Etapa': 'Con DEMUCA', 'Sesiones': (sessions['demuca_evaluations'] > 0).sum()},
])
display(coverage)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(coverage['Etapa'], coverage['Sesiones'], color='#2563eb')
ax.set(title='Cobertura del dataset', ylabel='Numero de sesiones', ylim=(0, len(sessions)))
ax.tick_params(axis='x', rotation=25)
plt.tight_layout()
plt.show()
"""),
        cell("markdown", """
## 3. Distribucion de eventos
"""),
        cell("code", """
events = pd.DataFrame(all_events)
if events.empty:
    print('No hay eventos anotados en el dataset.')
else:
    event_summary = events.groupby(['modality', 'type']).size().rename('eventos').reset_index()
    display(event_summary.sort_values(['modality', 'eventos'], ascending=[True, False]))
    by_modality = events['modality'].value_counts()
    by_modality.plot(kind='bar', color=['#2563eb', '#f59e0b', '#0891b2'], title='Eventos por modalidad')
    plt.ylabel('Numero de eventos')
    plt.tight_layout()
    plt.show()
"""),
        cell("markdown", """
## 4. Evaluaciones DEMUCA disponibles
"""),
        cell("code", """
responses = pd.DataFrame(all_responses)
if responses.empty:
    print('No hay respuestas DEMUCA en el dataset.')
else:
    responses['score'] = pd.to_numeric(responses['score'])
    demuca_summary = responses.groupby('category', as_index=False)['score'].agg(['count', 'mean']).reset_index()
    display(demuca_summary)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(demuca_summary['category'], demuca_summary['mean'], color='#16a34a')
    ax.set(xlim=(0, 2), xlabel='Puntaje promedio (0-2)', title='DEMUCA por categoria disponible')
    plt.tight_layout()
    plt.show()
"""),
        cell("markdown", """
## 5. Limitaciones

Las sesiones sin procesamiento o anotaciones representan datos pendientes, no valores cero.
Las evaluaciones DEMUCA existentes deben respetar su estado de revision clinica. Antes de
entrenar modelos se requieren mas sesiones independientes, anotaciones revisadas y division
por paciente para evitar fuga de informacion.
"""),
    ])


def write_notebook(path: Path, content: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    sessions = sorted(path for path in SESSIONS_DIR.iterdir() if path.is_dir())
    for session_dir in sessions:
        session_id = session_dir.name
        write_notebook(session_dir / "analitics" / f"EDA_{session_id}.ipynb", individual_notebook(session_id))
    write_notebook(ROOT / "analitics" / "EDA_DATASET.ipynb", dataset_notebook())
    print(f"Cuadernos individuales creados: {len(sessions)}")
    print(f"Cuaderno general creado: {ROOT / 'analitics' / 'EDA_DATASET.ipynb'}")


if __name__ == "__main__":
    main()
