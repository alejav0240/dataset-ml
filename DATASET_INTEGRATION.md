# Integración del dataset DEMUCA con el pipeline ML

Este repositorio es la fuente de estructura, metadatos y anotaciones del pipeline; no es un almacén de grabaciones. El directorio dataset/ y los formatos multimedia están excluidos por .gitignore. Las grabaciones y artefactos derivados deben montarse en un volumen privado, en almacenamiento de objetos o en una copia local con controles de acceso.

## Contrato canónico

La integración se describe en:

- contracts/dataset-source.json: instancia versionada del contrato.
- contracts/dataset-source.schema.json: esquema que valida la instancia.
- schemas/session.schema.json: metadatos mínimos por sesión.
- config/dataset.yaml: ventanas, modalidades y vocabularios.
- config/annotation_schema.yaml: atributos permitidos para eventos.

La ruta canónica de una sesión es:

```text
<DEMUCA_DATASET_ROOT>/dataset/sessions/<SESSION_ID>/
├── metadata/session.json
├── raw/
├── processed/features/
└── annotations/
   ├── visual/events.json
   ├── audio/events.json
   ├── interaction/events.json
   └── demuca/evaluations.json
```

El código histórico también genera <root>/sessions y el pipeline integrado admite <root>/dataset/dataset/sessions. Esas rutas son compatibilidad, no una segunda fuente de verdad.

## Conexión con ml-cbm

En el checkout del repositorio ML:

```bash
export DEMUCA_DATASET_ROOT=/data/dataset-ml
python audit_dataset.py --sessions-dir /data/dataset-ml/dataset/sessions
python prepare_dataset.py \
  --sessions-dir /data/dataset-ml/dataset/sessions \
  --task-config task.json \
  --out artifacts/event-windows.csv
```

El adaptador de resolución de rutas del pipeline también acepta el checkout directamente y busca, en orden, dataset/sessions, sessions y la ruta legacy dataset/dataset/sessions.

## Reglas de seguridad y validez

- Los IDs de paciente son seudónimos y se extraen del participante con rol PACIENTE; nunca se copian nombres.
- Las preanotaciones y los ejemplos (es_ejemplo=true) no son ground truth.
- La preparación falla si faltan revisión humana, guía aprobada, hashes de procedencia, features o consentimiento/aprobaciones del pipeline.
- Las evaluaciones DEMUCA se conservan como evidencia clínica revisada; no son el objetivo automático de este MVP.
- El dataset no se declara listo para entrenamiento por tener 17 sesiones técnicas: la partición debe hacerse por paciente y con evidencia independiente.

## Verificación local

```bash
python -m json.tool contracts/dataset-source.json
python -m unittest scripts.test_analizar_dataset
```

La ausencia de dataset/sessions en un clon fresco es esperada hasta montar el volumen privado de datos.
