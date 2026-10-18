# Análisis del dataset DEMUCA

Fecha de auditoría: 2026-10-06

## Resultado ejecutivo

- Sesiones detectadas: **2** (`S001`, `S998`).
- Sesiones estructuralmente válidas: **2**.
- Sesiones con pipeline técnico completo: **1** (`S001`).
- Sesiones listas para entrenamiento: **0**.
- Duración de material procesado: **24,01 minutos**.

## S001

El material técnico está completo y es internamente coherente:

- Video procesado: H.264, 1280x720, 10 fps, 1440,50 s.
- Audio procesado: PCM mono, 16 kHz, 1440,47 s.
- Frames extraídos: 1441 (aproximadamente 1 fps).
- Ventanas de audio: 1440.
- Energía RMS media: 0,059443.
- Tasa de cruces por cero media: 0,061849.
- Intensidad de movimiento media: 14,690260.

La sesión aún no es utilizable como muestra supervisada. Los 15 eventos y la única
evaluación DEMUCA están marcados con `"es_ejemplo": true`; por tanto hay **0
anotaciones reales**. Nueve eventos son preanotaciones provisionales derivadas de
señales o muestras visuales y requieren revisión experta. Las 14 respuestas DEMUCA
son contenido demostrativo y no deben tratarse como evaluación clínica definitiva.

## S998

Es una sesión vacía/de prueba: no tiene medios, features ni anotaciones y el
pipeline está pendiente. Debe completarse con una grabación real o mantenerse
fuera de cualquier partición de entrenamiento, validación o prueba.

## Conclusión

La canalización técnica funciona para `S001`, pero el conjunto todavía no posee
datos etiquetados reales ni volumen suficiente para entrenar o evaluar un modelo.
El siguiente hito obligatorio es realizar y revisar la anotación clínica de
`S001`, retirar la marca `es_ejemplo` únicamente en observaciones verificadas y
agregar más sesiones independientes.

La revisión de coherencia DEMUCA está documentada en
`dataset/sessions/S001/annotations/demuca/COHERENCE_REVIEW.md`: los puntajes del
ejemplo son aritméticamente correctos, pero no tienen soporte observacional
suficiente en los eventos actuales y permanecen en revisión clínica.

El diagnóstico se puede reproducir con:

```bash
./main.py validar
./main.py analizar
./main.py analizar --json
```
