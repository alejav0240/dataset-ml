---
title: "Avance v1: pipeline multimodal DEMUCA"
subtitle: "De sesiones de musicoterapia a evidencias temporales auditables"
author: "Proyecto DEMUCA"
date: "Octubre 2026"
---

# Objetivo del avance

Construir la primera versión reproducible del pipeline que transforma una sesión de musicoterapia en datos temporales estructurados para revisión clínica.

- Integra audio, video, movimiento y anotaciones temporales.
- Conserva la evidencia asociada a cada observación.
- Prepara el dataset para futura anotación y entrenamiento supervisado.

> El sistema apoya la observación; no reemplaza al musicoterapeuta ni emite diagnósticos.

# Arquitectura objetivo

```text
Sesión audiovisual
        |
Captura, ingesta y validación
        |
Normalización y segmentación temporal
        |
Audio ---------------------- Movimiento visual
        |                          |
        +---- Fusión de evidencias -+
                       |
          Anotación y revisión humana
                       |
      Futuro: modelo temporal e indicadores DEMUCA
```

La arquitectura contempla modelos de visión, audio y predicción clínica. La v1 se concentra en la base técnica y trazable necesaria antes de entrenarlos.

# Alcance implementado en v1

| Módulo | Entregable actual |
|---|---|
| Dataset | Estructura canónica por sesión y metadatos |
| Validación | Esquemas, vocabularios y coherencia temporal |
| Preprocesamiento | Video 1280x720 a 10 fps y audio mono a 16 kHz |
| Audio | RMS y ZCR por ventanas de 1 segundo |
| Movimiento | Intensidad global entre frames a 1 fps |
| Fusión inicial | Priorización multimodal de ventanas de revisión |
| Anotación | Eventos visuales, audio, interacción y DEMUCA |

# Flujo ejecutable

```text
Raw MP4
  -> procesar
  -> extraer-frames
  -> extraer-features
  -> preparar-anotacion
  -> validar y analizar
```

```bash
./main.py pipeline S001
./main.py preparar-anotacion S001
./main.py validar
./main.py analizar
```

Cada etapa genera archivos persistentes, con timestamps compatibles entre audio, video, features y anotaciones.

# Pipeline de sonido v1

**Entrada:** audio procesado WAV, mono, 16 kHz.

- Segmentación en ventanas de 1 segundo.
- **RMS:** resume la energía acústica de cada ventana.
- **ZCR:** cuantifica los cruces por cero de la señal.
- Salida: `processed/features/audio_features.json`.

Estas señales permiten localizar cambios de actividad sonora y priorizar fragmentos para revisión humana. No clasifican aún hablantes, emociones ni estados clínicos.

# Pipeline de movimiento v1

**Entrada:** frames del video procesado, muestreados a 1 fps.

- Conversión a escala de grises y reducción a 320x180.
- Suavizado para reducir variaciones menores.
- Diferencia absoluta entre frames consecutivos.
- Salida: `processed/features/visual_motion.json`.

La señal resultante mide movimiento global. La detección de pose, mirada, instrumentos y actores pertenece a las siguientes iteraciones.

# Fusión multimodal inicial

Las señales se agregan en ventanas de revisión de 30 segundos:

```text
score_prioridad = 0.4 * RMS normalizado
                + 0.4 * movimiento medio normalizado
                + 0.2 * pico de movimiento normalizado
```

- Produce una cola ordenada de ventanas para observación humana.
- Conserva RMS medio, ZCR medio, movimiento medio y pico de movimiento.
- No genera etiquetas clínicas ni predicciones DEMUCA.

# Demostración: sesión S001

| Indicador | Resultado |
|---|---:|
| Duración procesada | 24,01 min |
| Video | H.264, 1280x720, 10 fps |
| Audio | PCM mono, 16 kHz |
| Frames visuales | 1.441 |
| Ventanas acústicas | 1.440 |
| Ventanas de revisión | 49 |
| RMS medio | 0,059443 |
| ZCR medio | 0,061849 |
| Movimiento medio | 14,690260 |

La sesión está procesada y sus derivados son internamente coherentes.

# Evidencia y trazabilidad

Cada sesión organiza el material de origen, sus derivados y las anotaciones:

```text
sessions/S001/
  raw/audio/  raw/video/
  processed/audio/  processed/frames/  processed/features/
  annotations/audio/  annotations/visual/
  annotations/interaction/  annotations/demuca/
  metadata/session.json
```

Las anotaciones vinculan un evento o una valoración DEMUCA con su intervalo temporal y la evidencia audiovisual correspondiente.

# Estado actual y límites explícitos

- Se detectan 2 sesiones: `S001` y `S998`.
- Ambas son estructuralmente válidas.
- `S001` tiene pipeline técnico completo; `S998` es una sesión vacía de prueba.
- Hay 6 eventos y 1 evaluación DEMUCA demostrativos, todos marcados `es_ejemplo: true`.
- Existen 0 anotaciones reales y 0 sesiones listas para entrenamiento.
- Por ello, esta v1 no declara precisión, F1 ni capacidad de predicción clínica.

# Próximos pasos

1. Anotar y revisar `S001` con profesionales, conservando evidencia temporal.
2. Incorporar sesiones independientes y separar particiones por paciente.
3. Añadir features de audio: pitch, MFCC, tempo, ritmo y actividad de voz.
4. Añadir visión: pose, seguimiento de actores, mirada e instrumentos.
5. Entrenar un baseline supervisado de fusión, por ejemplo Random Forest.
6. Evaluar el modelo en sesiones y pacientes no vistos antes.

# Cierre

**La v1 ya convierte una sesión audiovisual en evidencia temporal estructurada, reproducible y lista para revisión humana.**

El próximo hito no es automatizar decisiones clínicas: es construir ground truth revisado que permita entrenar y evaluar modelos de manera responsable.

## Demo en vivo

```bash
cd /home/javi/Proyectos/cbm-front/dataset
./main.py validar
./main.py analizar
```

Resultado esperado: 2 sesiones estructuralmente válidas, 1 procesada y 0 listas para entrenamiento.
