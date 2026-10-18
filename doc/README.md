# Contrato del dataset multimodal DEMUCA

Este documento reúne los valores comprobados en los esquemas, configuración,
validador y catálogo DEMUCA del backend. Es la referencia para incorporar sesiones
y producir anotaciones consistentes.

> **Alcance de “validado”:** significa válido para la implementación actual. La
> interpretación y puntuación DEMUCA requieren revisión de un profesional; este
> documento no constituye una validación clínica de la escala ni del modelo.

## 1. Estado y versión

| Campo | Valor |
|---|---|
| Nombre | Dataset multimodal de musicoterapia DEMUCA |
| Versión | `0.1.0` |
| Unidad temporal de anotación | Evento |
| Ventana de entrada al modelo | 5 segundos |
| Ventana de contexto/revisión | 30 segundos |
| Video procesado | 1280×720, 10 fps |
| Audio procesado | WAV, mono, 16 kHz |
| Escala temporal | Segundos desde el inicio del video original |

Estado auditado el 2026-09-27:

- `S001`: pipeline técnico completo; anotaciones existentes solo de ejemplo.
- `S998`: sesión vacía/de prueba.
- Sesiones listas para entrenamiento: **0**.

## 2. Estructura canónica

```text
dataset/sessions/SNNN/
├── metadata/session.json
├── raw/
│   ├── video/
│   └── audio/
├── processed/
│   ├── video/
│   ├── audio/
│   ├── frames/
│   └── features/
├── annotations/
│   ├── visual/events.json
│   ├── audio/events.json
│   ├── interaction/events.json
│   ├── demuca/evaluations.json
│   └── review/annotation_tasks.tsv
└── README.md
```

El archivo original es la fuente de verdad. Los archivos de `processed/` son
derivados reproducibles y no deben reemplazar el original.

## 3. Identificadores y participantes

### Sesiones

- Formato obligatorio: `S` seguido de al menos tres dígitos.
- Válidos: `S001`, `S998`, `S1000`.
- Inválidos: `1`, `SES001`, `S01`.
- El `session_id` interno debe coincidir con el nombre del directorio.

### Participantes

Roles permitidos:

| Valor | Uso |
|---|---|
| `PACIENTE` | Persona evaluada |
| `TERAPEUTA` | Musicoterapeuta o educador principal |
| `OTRO` | Familiar, par u otra persona identificada |
| `DESCONOCIDO` | Persona cuyo rol no puede determinarse |

Usar identificadores seudónimos estables como `P001`, `T001` y `O001`. Nunca
guardar nombres, documentos u otros identificadores personales en anotaciones.

## 4. Reglas comunes de eventos

Todo archivo de eventos tiene esta forma:

```json
{
  "session_id": "S001",
  "events": []
}
```

Campos comunes de cada evento:

| Campo | Tipo | Regla |
|---|---|---|
| `start_seconds` | número | Obligatorio; mayor o igual que 0 |
| `end_seconds` | número | Obligatorio; mayor o igual que `start_seconds` |
| `type` | texto | Uno de los valores permitidos para la modalidad |
| `participant` | texto | Actor visual o de interacción, cuando corresponde |
| `speaker` | texto | Emisor de audio, cuando corresponde |
| `participants` | lista | Participantes de una actividad conjunta |
| `attributes` | objeto | Solo atributos admitidos para el tipo |
| `es_ejemplo` | booleano | `true` excluye el elemento del ground truth real |

El final no puede superar la duración de la sesión, salvo el margen técnico de 2
segundos aceptado por el validador. Para anotación humana debe mantenerse dentro de
la duración exacta.

## 5. Vocabulario visual

### Tipos permitidos

`MOVIMIENTO`, `MOVIMIENTO_REPETITIVO`, `CONTACTO_VISUAL`,
`INTERACCION_OBJETO`, `ORIENTACION_CORPORAL`.

### `MOVIMIENTO`

Requiere `participant`.

| Atributo | Valores permitidos |
|---|---|
| `intensidad` | `BAJO`, `MEDIO`, `ALTO` |
| `parte_cuerpo` | `CABEZA`, `BRAZO`, `MANO`, `TORSO`, `PIERNA`, `CUERPO_ENTERO`, `OTRO` |

```json
{
  "start_seconds": 12.4,
  "end_seconds": 15.8,
  "type": "MOVIMIENTO",
  "participant": "P001",
  "attributes": {"intensidad": "MEDIO", "parte_cuerpo": "BRAZO"}
}
```

### `MOVIMIENTO_REPETITIVO`

Requiere `participant`.

| Atributo | Valores permitidos |
|---|---|
| `type` | `MANO`, `BRAZO`, `CABEZA`, `CUERPO`, `OTRO` |
| `frecuencia` | `BAJA`, `MEDIA`, `ALTA` |

### `CONTACTO_VISUAL`

Requiere `participant`.

| Atributo | Valores permitidos |
|---|---|
| `objetivo` | `PACIENTE`, `TERAPEUTA`, `OBJETO`, `CAMARA`, `OTRO` |

La orientación de cabeza por sí sola no demuestra contacto visual. Si los ojos no
son visibles, usar `ORIENTACION_CORPORAL` o dejar el caso para revisión.

### `INTERACCION_OBJETO`

Requiere `participant`.

| Atributo | Valores permitidos |
|---|---|
| `accion` | `TOCAR`, `AGARRAR`, `SOSTENER`, `MOVER`, `USAR`, `SOLTAR` |
| `tipo_objeto` | `TAMBOR`, `GUITARRA`, `PIANO`, `MARACA`, `JUGUETE`, `OTRO` |

### `ORIENTACION_CORPORAL`

Requiere `participant`. No tiene atributos categóricos cerrados; registrar tiempos,
tipo y participante. No crear valores libres dentro de `attributes`.

## 6. Vocabulario de audio

### Tipos permitidos

`VOCALIZACION`, `HABLA`, `RISA`, `LLANTO`, `GRITO`, `SILENCIO`,
`ACTIVIDAD_MUSICAL`.

### `VOCALIZACION`

Requiere `speaker`.

| Atributo | Valores permitidos |
|---|---|
| `type` | `VOCALIZACION`, `BALBUCEO`, `HABLA`, `OTRO` |

### `ACTIVIDAD_MUSICAL`

| Atributo | Valores permitidos |
|---|---|
| `type` | `TERAPEUTA_TOCANDO`, `PACIENTE_TOCANDO`, `TOCANDO_JUNTOS`, `MUSICA_GRABADA`, `CANTO`, `ACTIVIDAD_RITMICA` |

### Eventos sin atributos cerrados

- `HABLA`
- `RISA`
- `LLANTO`
- `GRITO`
- `SILENCIO`

`HABLA` requiere `speaker`. Para los demás tipos, registrar el hablante cuando pueda
identificarse. No agregar atributos libres.

## 7. Vocabulario de interacción

Tipos permitidos:

| Tipo | Observación operacional |
|---|---|
| `MIRADA` | Orientación visual interpersonal observable |
| `GESTO` | Gesto comunicativo dirigido |
| `TACTO` | Contacto físico interpersonal |
| `IMITACION` | Repetición observable de una acción previa |
| `RESPUESTA` | Conducta vinculada temporalmente a una acción concreta |
| `ACTIVIDAD_CONJUNTA` | Ambos participantes intervienen en la actividad |
| `INTERACCION_MUSICAL` | Intercambio mediante sonido, ritmo o instrumento |
| `INTERACCION_VERBAL` | Intercambio verbal entre participantes |

Estos tipos todavía no tienen atributos categóricos cerrados. No crear atributos
ad hoc: usar `participant`, `participants` y notas de revisión según corresponda.

## 8. Catálogo DEMUCA del backend

El backend define 40 subescalas, todas con `max_score = 2`. Los únicos puntajes
admitidos para el dataset son enteros `0`, `1` y `2`. El significado clínico exacto
de cada puntaje debe confirmarse con el manual y el evaluador responsable; no debe
deducirse únicamente como “no/poco/mucho”.

### Comportamientos Restrictivos

1. Estereotipias
2. Agresividad
3. Desinterés
4. Pasividad
5. Resistencia
6. Reclusión / Aislamiento
7. Berrinche

### Interacción Social y Cognición

8. Contacto Visual
9. Comunicación Verbal
10. Interacción con Instrumentos
11. Interacción con Otros Objetos
12. Interacción con Educador / Musicoterapeuta
13. Interacción con Padres
14. Interacción con Pares
15. Atención
16. Imitación

### Percepción y Exploración Rítmica

17. Pulso Interno
18. Regulación Temporal
19. Apoyo Rítmico
20. Ritmo Real
21. Contrastes de Tempo

### Percepción y Exploración Sonora

22. Sonido Silencio
23. Timbre
24. Planos de Altura
25. Movimiento Sonoro
26. Contrastes de Intensidad
27. Repetición de Ideas Rítmicas o Melódicas
28. Sentido de Conclusión

### Exploración Vocal

29. Vocalizaciones
30. Balbuceos
31. Sílabas Canónicas
32. Imitación de Canciones
33. Creación Vocal

### Movimiento Corporal con la Música

34. Andar
35. Correr
36. Parar
37. Bailar
38. Saltar
39. Gesticular
40. Moverse en el Sitio

Una evaluación completa tiene máximo teórico `80` si se responden las 40
subescalas. Una evaluación parcial debe declarar solo las respuestas observadas y
calcular `max_total_score` como la suma de sus `max_score`; no debe rellenar una
conducta no observada como cero sin criterio clínico.

## 9. Formato DEMUCA

```json
{
  "session_id": "S001",
  "evaluations": [
    {
      "scale": "Escala DEMUCA",
      "scale_type": "subscale",
      "patient_id": "P001",
      "evaluator_id": "E001",
      "evaluated_at": "2026-09-27T15:30:00-04:00",
      "responses": [
        {
          "subscale": "Contacto Visual",
          "category": "Interacción Social y Cognición",
          "score": 1,
          "max_score": 2,
          "evidence": [
            {
              "modality": "visual",
              "start_seconds": 121.2,
              "end_seconds": 124.7,
              "description": "Descripción observable y neutral."
            }
          ]
        }
      ],
      "total_score": 1,
      "max_total_score": 2,
      "notes": "Evaluación revisada por el profesional responsable."
    }
  ]
}
```

Reglas aritméticas comprobadas por el validador:

- `total_score` = suma de todos los `score`.
- `max_total_score` = suma de todos los `max_score`.
- Cada evidencia respeta el orden y los límites temporales de la sesión.
- La evidencia describe algo observable; no debe ser una conclusión circular que
  simplemente repita la puntuación.

## 10. Estados de anotación

Estados de las tareas de revisión:

| Estado | Significado |
|---|---|
| `pending` | Ventana todavía no revisada |
| `done` | Las modalidades aplicables fueron revisadas |
| `needs_clinical_review` | Existe ambigüedad o requiere decisión profesional |

Campos de trazabilidad mínimos en `annotation_tasks.tsv`:

- `task_id`
- `session_id`
- `start_seconds`, `end_seconds`
- `status`
- `annotator_primary`
- `reviewer`
- `guide_version`
- `notes`

Las columnas de RMS, ZCR, movimiento y prioridad sirven para ordenar el trabajo;
**no son etiquetas** y no prueban una conducta clínica.

## 11. Protocolo mínimo de anotación

1. Ver la ventana completa antes de decidir.
2. Marcar únicamente conductas observables y utilizar vocabulario cerrado.
3. Separar eventos cuando exista una interrupción clara de al menos un segundo.
4. Permitir solapamientos cuando representen modalidades o conductas diferentes.
5. Marcar la incertidumbre; nunca forzar una categoría.
6. Ejecutar `./main.py validar` después de cada lote.
7. Una segunda persona anota independientemente al menos una muestra estratificada
   del 20 %.
8. Resolver discrepancias y conservar trazabilidad de la adjudicación.
9. La evaluación DEMUCA final debe estar firmada/revisada por el profesional.

## 12. Criterio para considerar una sesión lista

Una sesión está lista para entrenamiento solo cuando:

- los medios originales están presentes y seudonimizados;
- video, audio, frames y features terminaron correctamente;
- las tres modalidades fueron revisadas o declaradas no aplicables;
- existe al menos una anotación real, no marcada `es_ejemplo`;
- todos los eventos pasan el validador;
- la revisión secundaria y las discrepancias están documentadas;
- la evaluación DEMUCA, si se utiliza como objetivo, tiene revisión clínica;
- no contiene información personal identificable;
- está asignada a una partición por paciente, no por ventanas.

## 13. Comandos de control

```bash
cd /home/javi/Proyectos/cbm-front/dataset

# Integridad estructural, tiempos, vocabularios y sumas
./main.py validar

# Cobertura y preparación para entrenamiento
./main.py analizar

# Preparar ventanas de revisión humana
./main.py preparar-anotacion S001

# Abrir la herramienta audiovisual de anotación
./main.py anotar

# Exportar línea temporal
./main.py exportar S001
```

## 14. Fuentes internas de verdad

- Metadata: `schemas/session.schema.json`
- Eventos y atributos: `config/annotation_schema.yaml`
- Parámetros técnicos: `config/dataset.yaml`
- Catálogo DEMUCA: `backend/evaluations/management/commands/seed_scales.py`
- Reglas ejecutables: `scripts/validar_dataset.py`
- Guía de decisión: `GUIA_ANOTACION.md`
- Plan de incorporación: `PLAN_ANOTACION.md`
- Prompt de preanotación con IA: `doc/PROMPT_ANOTACION_IA.md`

Si dos fuentes difieren, no agregar datos nuevos hasta reconciliarlas y actualizar
el esquema, el validador y este documento en el mismo cambio.
