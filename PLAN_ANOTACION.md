# Plan de preparación del dataset DEMUCA

## Objetivo

Convertir `S001` en una sesión anotada y revisada por personas, sin tratar las
anotaciones demostrativas actuales como verdad clínica, y dejar un flujo repetible
para las sesiones siguientes.

## Fase 1 — Preparar el trabajo para S001 (cerrada)

- [x] Separar validación estructural de preparación para entrenamiento.
- [x] Identificar ejemplos mediante `es_ejemplo`.
- [x] Crear una cola reproducible de ventanas temporales para revisión.
- [x] Registrar la anotación primaria, la revisión y la aprobación profesional
  informadas por el equipo.
- [x] Aprobar la guía S001 v1.0 con reglas y ejemplos para las 20 etiquetas.

**Salida:** `annotations/review/annotation_tasks.tsv`, generado con
`./main.py preparar-anotacion S001`.

## Fase 2 — Anotación primaria (S001 reportada como completa)

1. [x] Revisar las ventanas en orden de `priority_rank`.
2. [x] Registrar eventos observables en visual, audio e interacción.
3. [x] Usar `status=done` solamente cuando las tres modalidades estén revisadas.
4. [x] Usar `status=needs_clinical_review` cuando exista ambigüedad; no inferir
   diagnósticos ni completar puntuaciones DEMUCA automáticamente.
5. [x] Registrar anotador, revisor, versión de guía y fechas en la cola y en el
   archivo de aprobación. El identificador primario registrado es `alejandro_dev`.

**Criterio de salida:** 100 % de las ventanas revisadas y ningún evento real con
tiempos, participantes o vocabularios inválidos.

## Fase 3 — Revisión y acuerdo (aprobación S001 registrada)

- [x] Erik revisó la anotación de S001; el equipo informa que no tuvo observaciones.
- [ ] Registrar métricas de acuerdo por modalidad y tipo de evento para una muestra
  estratificada independiente de al menos el 20 % de las ventanas.
- Resolver desacuerdos conservando las dos anotaciones originales y la decisión
  adjudicada.
- Un profesional autorizado revisa y firma la evaluación DEMUCA final.

La aprobación comunicada por el equipo no sustituye el cálculo de acuerdo ni la
aprobación de una evaluación DEMUCA final. Esos elementos siguen fuera del cierre
del estado de anotación observable de S001.

**Criterio de salida:** discrepancias resueltas y evaluación clínica trazable.

## Fase 4 — Cierre de S001

- [x] Ejecutar `./main.py validar`; las 17 sesiones pasan validación estructural.
- [x] Confirmar mediante `./main.py analizar --json` que S001 tiene procesamiento
  completo y anotaciones.
- [x] Corregir la etiqueta del informe: tener procesamiento y anotaciones sólo
  produce una sesión candidata; no implica autorización de entrenamiento.
- [ ] Resolver el evento no verificado y calcular acuerdo independiente; no borrar
  `source`, `es_ejemplo` ni notas de procedencia de los JSON aprobados.
- [ ] Exportar la línea temporal sólo para flujos internos autorizados; no usar ese
  artefacto como autorización para entrenar.

## Fase 5 — Escalar el dataset

- Incorporar sesiones independientes y aplicar el mismo protocolo.
- Asignar particiones por paciente, nunca por ventanas del mismo video, para evitar
  fuga de identidad y contexto entre entrenamiento y evaluación.
- Mantener consentimientos, seudonimización, acceso restringido y registro de
  versiones fuera de los archivos utilizados para modelado.
- [x] Registrar la autorización de `alejandro_dev` para usar S001 en las fases
  internas del proyecto y en investigación, desarrollo, pruebas y evaluación de
  modelos (`annotations/review/annotation_approval.json`).
- [x] Extender la autorización del usuario del proyecto para uso interno hasta S008
  inclusive; las sesiones S002–S008 requieren procesamiento y revisión propios y no
  quedan aprobadas como anotaciones por esta autorización.
- [x] Aprobar el objetivo de predicción event-occurrence de `ml/task.json` para
  investigación y evaluación interna; no incluye DEMUCA ni diagnósticos.
- [x] Registrar la autorización de uso para S001 declarada por `alejandro_dev`, quien
  informa que el consentimiento se gestionó con terapeutas y el Centro Boliviano de
  Musicotepatia, La Paz, en 2026. No se aportó referencia documental; el registro es
  una atestación del responsable del proyecto, no una verificación legal independiente.
- No entrenar un modelo hasta contar con suficiente diversidad de participantes y
  una partición de evaluación independiente.

## Próxima acción humana

La guía S001 v1.0 y la aprobación de las anotaciones están registradas en
`dataset/dataset/sessions/S001/annotations/review/`. La cola existente se cerró sin
regenerarla. Quedan por registrar métricas de acuerdo; estas tareas no autorizan
por sí solas el entrenamiento. `alejandro_dev` autorizó el uso interno de S001 en
las fases del proyecto y modelos, y aprobó el objetivo de predicción. Las aprobaciones
de revisión y consentimiento están acotadas a S001; el consentimiento se registra como
atestación del responsable, sin referencia documental independiente. Faltan suficientes
pacientes para la partición y métricas independientes de acuerdo.

`GUIA_ANOTACION_TEMPLATE.md` ofrece un borrador vacío con la taxonomía técnica y
campos para completar y aprobar. No reemplaza esta planificación ni constituye
una guía operativa hasta que las personas autorizadas completen su aprobación.
La carpeta `dataset/dataset/sessions/S001/annotations/review/` contiene el inventario
retrospectivo, `annotation_guide.md` v1.0 y `annotation_approval.json` con hashes de
los eventos revisados. La plantilla reutilizable para otras sesiones permanece en
`dataset/GUIA_ANOTACION_TEMPLATE.md`. Para validar la estructura de la guía:

```bash
python dataset/scripts/validar_guia_anotacion.py --guide path/to/approved-guide.md
```
