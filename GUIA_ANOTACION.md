# Guía operativa de anotación DEMUCA — borrador 0.1

Esta guía describe eventos observables. No autoriza inferencias diagnósticas ni
sustituye el criterio de un profesional habilitado para puntuar DEMUCA.

## Reglas generales

1. Ver la ventana completa una vez antes de etiquetar.
2. En la segunda reproducción, marcar inicio y fin del comportamiento observable
   con precisión de décimas de segundo.
3. Usar el identificador `P001` o `T001`; no escribir nombres personales.
4. Se permiten eventos simultáneos y solapados cuando representan modalidades o
   conductas distintas.
5. No etiquetar una conducta inferida, fuera de cámara o inaudible.
6. Si no hay evidencia suficiente, dejar la tarea en
   `needs_clinical_review` y explicar la duda en `notes`.
7. No copiar los eventos con `es_ejemplo: true` como si fueran observaciones.

## Límites temporales

- **Inicio:** primer instante donde la conducta es observable.
- **Fin:** primer instante posterior donde deja de observarse.
- Separar dos eventos cuando existe una interrupción clara de al menos 1 segundo.
- Un evento que cruza dos ventanas se anota una sola vez con sus tiempos reales.

## Modalidad visual

- `MOVIMIENTO`: movimiento corporal identificable. Registrar `intensidad` y
  `parte_cuerpo` usando exclusivamente los valores del esquema.
- `MOVIMIENTO_REPETITIVO`: patrón motor repetido; no usar para un único gesto.
- `CONTACTO_VISUAL`: orientación visual observable hacia una persona u objetivo;
  evitar asumir atención cuando los ojos no son visibles.
- `INTERACCION_OBJETO`: contacto o acción física con un objeto. Registrar acción y
  tipo de objeto.
- `ORIENTACION_CORPORAL`: cambio o mantenimiento claro de orientación corporal.

## Modalidad de audio

- `VOCALIZACION`: emisión vocal no clasificada como risa, llanto o grito.
- `HABLA`: producción verbal inteligible; no transcribir datos personales.
- `RISA`, `LLANTO`, `GRITO`: usar solo cuando el patrón acústico sea distinguible.
- `SILENCIO`: reservar para intervalos analíticamente relevantes, no llenar toda
  ausencia breve de voz.
- `ACTIVIDAD_MUSICAL`: sonido musical o actividad rítmica observable. Identificar
  quién toca cuando sea posible.

## Modalidad de interacción

- `MIRADA`: orientación visual interpersonal observable.
- `GESTO`: gesto comunicativo dirigido a otra persona.
- `TACTO`: contacto físico interpersonal observable.
- `IMITACION`: repetición observable de una acción previa de otra persona.
- `RESPUESTA`: conducta posterior y plausiblemente vinculada a una acción concreta;
  marcar para revisión si el vínculo temporal es ambiguo.
- `ACTIVIDAD_CONJUNTA`: ambos participantes intervienen en una misma actividad.
- `INTERACCION_MUSICAL`: intercambio mediante sonido, ritmo o instrumento.
- `INTERACCION_VERBAL`: intercambio verbal entre participantes.

## Flujo por tarea

1. Abrir `annotations/review/annotation_tasks.tsv` y elegir el menor
   `priority_rank` pendiente.
2. Revisar visual, audio e interacción.
3. Guardar los eventos en el JSON de la modalidad correspondiente.
4. Completar `annotator_primary`, `guide_version` y `notes`.
5. Cambiar a `done` o `needs_clinical_review`.
6. Ejecutar `./main.py validar` después de cada lote.

## Revisión

El revisor no debe ver las decisiones del anotador primario antes de registrar su
propia muestra. Las diferencias se adjudican posteriormente y se documenta la
razón. La puntuación DEMUCA final requiere revisión clínica independiente.
