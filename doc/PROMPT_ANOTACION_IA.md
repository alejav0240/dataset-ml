# Prompt para preanotación multimodal con IA

Este prompt sirve para enviar un fragmento de video con audio a un modelo multimodal
y obtener **propuestas de anotación** compatibles con el dataset DEMUCA.

La salida de la IA no es ground truth ni una evaluación clínica. Una persona debe
revisar el fragmento, corregir tiempos y categorías, y aprobar cada evento antes de
incorporarlo al dataset.

## Prompt listo para usar

```text
Actúa como asistente de preanotación audiovisual para un dataset de sesiones de
musicoterapia. Analiza solamente el fragmento adjunto y devuelve conductas
directamente observables o audibles.

No realices diagnósticos, no infieras estados mentales, intención, atención,
emociones ni puntuaciones clínicas. No asignes puntuaciones DEMUCA. Si una conducta
no es claramente visible o audible, no la inventes: regístrala en uncertainties.

CONTEXTO DEL FRAGMENTO

- session_id: {{SESSION_ID}}
- fragment_start_seconds: {{FRAGMENT_START_SECONDS}}
- fragment_end_seconds: {{FRAGMENT_END_SECONDS}}
- patient_id: {{PATIENT_ID}}
- therapist_id: {{THERAPIST_ID}}
- otros participantes: {{OTHER_PARTICIPANTS_OR_EMPTY}}
- descripción opcional del entorno: {{CONTEXT_OR_EMPTY}}

Los tiempos de salida deben ser ABSOLUTOS respecto del inicio de la sesión, no
relativos al fragmento. Deben cumplir:

fragment_start_seconds <= start_seconds <= end_seconds <= fragment_end_seconds

Analiza las tres modalidades por separado.

1. EVENTOS VISUALES PERMITIDOS

MOVIMIENTO
- participant obligatorio.
- attributes.intensidad: BAJO | MEDIO | ALTO.
- attributes.parte_cuerpo: CABEZA | BRAZO | MANO | TORSO | PIERNA |
  CUERPO_ENTERO | OTRO.

MOVIMIENTO_REPETITIVO
- participant obligatorio.
- attributes.type: MANO | BRAZO | CABEZA | CUERPO | OTRO.
- attributes.frecuencia: BAJA | MEDIA | ALTA.
- Usar únicamente cuando se observe repetición, no para un solo movimiento.

CONTACTO_VISUAL
- participant obligatorio.
- attributes.objetivo: PACIENTE | TERAPEUTA | OBJETO | CAMARA | OTRO.
- No confundir orientación de cabeza con contacto visual. Si los ojos no son
  visibles, usar ORIENTACION_CORPORAL o indicar incertidumbre.

INTERACCION_OBJETO
- participant obligatorio.
- attributes.accion: TOCAR | AGARRAR | SOSTENER | MOVER | USAR | SOLTAR.
- attributes.tipo_objeto: TAMBOR | GUITARRA | PIANO | MARACA | JUGUETE | OTRO.

ORIENTACION_CORPORAL
- participant obligatorio.
- Sin atributos adicionales.

2. EVENTOS DE AUDIO PERMITIDOS

VOCALIZACION
- speaker obligatorio.
- attributes.type: VOCALIZACION | BALBUCEO | HABLA | OTRO.

HABLA
- speaker obligatorio.
- Sin atributos adicionales.

RISA | LLANTO | GRITO | SILENCIO
- Sin atributos adicionales.
- Incluir speaker cuando sea identificable, excepto SILENCIO.

ACTIVIDAD_MUSICAL
- attributes.type: TERAPEUTA_TOCANDO | PACIENTE_TOCANDO | TOCANDO_JUNTOS |
  MUSICA_GRABADA | CANTO | ACTIVIDAD_RITMICA.
- Incluir speaker cuando corresponda y pueda identificarse.

No transcribas nombres, información personal ni conversaciones. Para HABLA solo
indica que existe habla; no incluyas su contenido.

3. EVENTOS DE INTERACCIÓN PERMITIDOS

MIRADA | GESTO | TACTO | IMITACION | RESPUESTA | ACTIVIDAD_CONJUNTA |
INTERACCION_MUSICAL | INTERACCION_VERBAL

- Usa participant para el actor principal cuando sea identificable.
- Usa participants para actividades que involucren a más de una persona.
- IMITACION requiere una acción previa observable que esté siendo reproducida.
- RESPUESTA requiere una conducta posterior claramente relacionada temporalmente
  con una acción observable de otra persona.
- No uses RESPUESTA solamente porque dos eventos ocurren cerca en el tiempo.

REGLAS DE ANOTACIÓN

1. Usa únicamente los tipos, atributos y valores escritos en este prompt.
2. No crees sinónimos, etiquetas nuevas ni valores en minúsculas.
3. Marca el inicio cuando la conducta comienza a ser observable y el final cuando
   deja de observarse.
4. Se permiten eventos simultáneos y solapados entre modalidades.
5. Separa dos eventos si existe una interrupción clara de al menos 1 segundo.
6. participant y speaker deben usar exclusivamente los identificadores entregados
   en el contexto.
7. Si no puedes distinguir paciente y terapeuta con suficiente seguridad, no
   adivines el identificador. Lleva el caso a uncertainties.
8. No conviertas energía acústica, movimiento de cámara, ruido, oclusiones o música
   de fondo en una conducta del paciente.
9. No clasifiques como CONTACTO_VISUAL cuando solo se observa el perfil, la nuca o
   una orientación aproximada de cabeza.
10. No uses las características físicas, la voz o el rostro para identificar a una
    persona fuera de los roles proporcionados.
11. confidence representa confianza observacional, no probabilidad clínica.
12. Si no hay eventos claros en una modalidad, devuelve una lista vacía.

Devuelve exclusivamente un objeto JSON válido, sin Markdown, explicaciones ni
texto adicional, con esta estructura exacta:

{
  "session_id": "{{SESSION_ID}}",
  "fragment": {
    "start_seconds": {{FRAGMENT_START_SECONDS}},
    "end_seconds": {{FRAGMENT_END_SECONDS}}
  },
  "visual": [
    {
      "start_seconds": 0.0,
      "end_seconds": 0.0,
      "type": "MOVIMIENTO",
      "participant": "{{PATIENT_ID}}",
      "attributes": {
        "intensidad": "MEDIO",
        "parte_cuerpo": "BRAZO"
      },
      "confidence": 0.0,
      "evidence_description": "Descripción neutral de lo que se ve."
    }
  ],
  "audio": [
    {
      "start_seconds": 0.0,
      "end_seconds": 0.0,
      "type": "VOCALIZACION",
      "speaker": "{{PATIENT_ID}}",
      "attributes": {
        "type": "VOCALIZACION"
      },
      "confidence": 0.0,
      "evidence_description": "Descripción neutral de lo que se oye."
    }
  ],
  "interaction": [
    {
      "start_seconds": 0.0,
      "end_seconds": 0.0,
      "type": "ACTIVIDAD_CONJUNTA",
      "participant": "{{PATIENT_ID}}",
      "participants": ["{{PATIENT_ID}}", "{{THERAPIST_ID}}"],
      "confidence": 0.0,
      "evidence_description": "Descripción neutral de la interacción observable."
    }
  ],
  "uncertainties": [
    {
      "start_seconds": 0.0,
      "end_seconds": 0.0,
      "modality": "visual | audio | interaction",
      "candidate_types": ["TIPO_1", "TIPO_2"],
      "reason": "Por qué no existe evidencia suficiente para decidir."
    }
  ],
  "quality": {
    "video": "BUENA | MEDIA | BAJA",
    "audio": "BUENA | MEDIA | BAJA",
    "occlusion": "NINGUNA | PARCIAL | ALTA",
    "background_noise": "BAJO | MEDIO | ALTO",
    "notes": "Problemas técnicos que pueden afectar la anotación."
  }
}

Antes de responder, verifica internamente:

- Que el JSON sea válido.
- Que todos los tiempos estén dentro del fragmento.
- Que end_seconds sea mayor o igual que start_seconds.
- Que no existan tipos o atributos fuera del vocabulario.
- Que todos los actores pertenezcan a los identificadores proporcionados.
- Que confidence esté entre 0 y 1.
- Que no hayas incluido una puntuación DEMUCA.
```

## Variables que deben sustituirse

| Variable | Ejemplo |
|---|---|
| `{{SESSION_ID}}` | `S001` |
| `{{FRAGMENT_START_SECONDS}}` | `690.0` |
| `{{FRAGMENT_END_SECONDS}}` | `720.0` |
| `{{PATIENT_ID}}` | `P001` |
| `{{THERAPIST_ID}}` | `T001` |
| `{{OTHER_PARTICIPANTS_OR_EMPTY}}` | `[]` |
| `{{CONTEXT_OR_EMPTY}}` | `Paciente y terapeuta frente a un tambor.` |

## Ejemplo de encabezado completado

```text
- session_id: S001
- fragment_start_seconds: 690.0
- fragment_end_seconds: 720.0
- patient_id: P001
- therapist_id: T001
- otros participantes: []
- descripción opcional del entorno: Paciente y terapeuta en una actividad musical.
```

## Proceso recomendado

1. Extraer un fragmento de 15–30 segundos conservando audio y video.
2. Sustituir todas las variables del prompt.
3. Enviar prompt y fragmento al modelo multimodal.
4. Validar sintácticamente el JSON devuelto.
5. Mostrar las propuestas en el anotador como pendientes, nunca como aprobadas.
6. Una persona revisa tiempos, actores, tipos y atributos observando el video.
7. Guardar solo los eventos aceptados y ejecutar `./main.py validar`.
8. Reservar la evaluación DEMUCA para el profesional responsable.

## Restricciones para entrenamiento

- Conservar la salida original del modelo separada del ground truth aprobado.
- Registrar nombre y versión del modelo, fecha, prompt y fragmento analizado.
- No entrenar y evaluar con ventanas del mismo paciente en particiones diferentes.
- No utilizar ejemplos generados por IA como etiquetas reales sin revisión humana.
- No enviar material clínico identificable a servicios externos sin autorización,
  consentimiento y controles de privacidad aplicables.
