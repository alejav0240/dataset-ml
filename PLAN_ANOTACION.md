# Plan de preparación del dataset DEMUCA

## Objetivo

Convertir `S001` en una sesión anotada y revisada por personas, sin tratar las
anotaciones demostrativas actuales como verdad clínica, y dejar un flujo repetible
para las sesiones siguientes.

## Fase 1 — Preparar el trabajo (iniciada)

- [x] Separar validación estructural de preparación para entrenamiento.
- [x] Identificar ejemplos mediante `es_ejemplo`.
- [x] Crear una cola reproducible de ventanas temporales para revisión.
- [ ] Confirmar quién realizará la anotación primaria y la revisión clínica.
- [ ] Definir las reglas operativas de cada etiqueta con ejemplos positivos,
  negativos y casos ambiguos.

**Salida:** `annotations/review/annotation_tasks.tsv`, generado con
`./main.py preparar-anotacion S001`.

## Fase 2 — Anotación primaria

1. Revisar las ventanas en orden de `priority_rank`.
2. Registrar eventos observables en visual, audio e interacción.
3. Usar `status=done` solamente cuando las tres modalidades estén revisadas.
4. Usar `status=needs_clinical_review` cuando exista ambigüedad; no inferir
   diagnósticos ni completar puntuaciones DEMUCA automáticamente.
5. Conservar el anotador, fecha, versión de guía y observaciones de cada tarea.

**Criterio de salida:** 100 % de las ventanas revisadas y ningún evento real con
tiempos, participantes o vocabularios inválidos.

## Fase 3 — Revisión y acuerdo

- Una segunda persona vuelve a anotar, como mínimo, una muestra estratificada del
  20 % de las ventanas (actividad alta, media y baja).
- Resolver desacuerdos conservando las dos anotaciones originales y la decisión
  adjudicada.
- Calcular acuerdo por modalidad y por tipo de evento. No mezclar una etiqueta
  adjudicada con ejemplos demostrativos.
- Un profesional autorizado revisa y firma la evaluación DEMUCA final.

**Criterio de salida:** discrepancias resueltas y evaluación clínica trazable.

## Fase 4 — Cierre de S001

- Exportar la línea temporal y ejecutar `./main.py validar`.
- Retirar `es_ejemplo` únicamente de observaciones verificadas o reemplazar los
  ejemplos por anotaciones reales.
- Actualizar los flags de `metadata/session.json` después de la revisión.
- Ejecutar `./main.py analizar`; `S001` debe aparecer como lista.

## Fase 5 — Escalar el dataset

- Incorporar sesiones independientes y aplicar el mismo protocolo.
- Asignar particiones por paciente, nunca por ventanas del mismo video, para evitar
  fuga de identidad y contexto entre entrenamiento y evaluación.
- Mantener consentimientos, seudonimización, acceso restringido y registro de
  versiones fuera de los archivos utilizados para modelado.
- No entrenar un modelo hasta contar con suficiente diversidad de participantes y
  una partición de evaluación independiente.

## Próxima acción humana

Asignar `annotator_primary` y `reviewer` y aprobar la guía de etiquetas. Mientras
eso ocurre, la cola generada permite comenzar la revisión observacional de `S001`
sin convertir resultados automáticos en etiquetas clínicas.

`GUIA_ANOTACION_TEMPLATE.md` ofrece un borrador vacío con la taxonomía técnica y
campos para completar y aprobar. No reemplaza esta planificación ni constituye
una guía operativa hasta que las personas autorizadas completen su aprobación.
Después de completar una copia, ejecutar este control estructural; el comando no
aprueba la guía:

```bash
python dataset/scripts/validar_guia_anotacion.py --guide path/to/approved-guide.md
```
