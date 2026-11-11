# Dataset Multimodal DEMUCA

Dataset multimodal para investigación sobre evaluación asistida por inteligencia artificial de sesiones de musicoterapia.

---

## 🚀 Guía Rápida: Agregar y Procesar una Nueva Sesión

Todo el flujo de trabajo está centralizado en el script principal [`./main.py`](file:///home/javi/Proyectos/cbm-front/dataset/main.py).

### Flujo paso a paso:

```text
[ 1. Crear ] ──> [ 2. Copiar Raw ] ──> [ 3. Pipeline / Procesar ] ──> [ 4. Anotar ] ──> [ 5. Validar ]
```

---

### Paso 1. Crear la estructura de la nueva sesión
Genera las carpetas, metadatos y esquemas base para la sesión (ej. `S002`):

```bash
cd dataset
./main.py crear S002
```

---

### Paso 2. Ubicar la grabación original
Copia o mueve el video de la sesión al directorio `raw` recién creado:

```text
dataset/sessions/S002/raw/
    └── S002_raw.mp4
```

Abre `dataset/sessions/S002/metadata/session.json` y confirma que la ruta de video esté asignada:
```json
"recording": {
    "original_video": "raw/S002_raw.mp4"
}
```

---

### Paso 3. Ejecutar el procesamiento automático

Puedes correr todo el pipeline en un solo paso:

```bash
./main.py pipeline S002
```

O si prefieres ejecutar cada etapa individualmente:

1. **Normalizar audio y video:**  
   *(Convierte video a 1280x720 10fps y audio a 16kHz mono WAV)*
   ```bash
   ./main.py procesar S002
   ```

2. **Extraer frames para análisis visual (1 fps):**  
   ```bash
   ./main.py extraer-frames S002
   ```

3. **Extraer características (RMS, ZCR, densidad de movimiento):**  
   ```bash
   ./main.py extraer-features S002
   ```

---

### Paso 4. Anotación y Evaluación Clínica

Edita o importa las anotaciones en la carpeta `annotations/`:
- `annotations/visual/events.json`: Movimientos corporales, interacción con objetos, etc.
- `annotations/audio/events.json`: Vocalizaciones, llanto, risa, actividad musical.
- `annotations/interaction/events.json`: Respuesta, miradas, turnos e imitación.
- `annotations/demuca/evaluations.json`: Evaluación de subescalas de la escala DEMUCA con evidencias temporales.

> **Tip para anotadores (ELAN / Praat):**  
> Puedes exportar las anotaciones a un formato TSV para cargarlas en herramientas de anotación visual:
> ```bash
> ./main.py exportar S002
> ```

---

### Paso 5. Validar la integridad del Dataset

Comprueba que todas las sesiones cumplan los esquemas JSON, no tengan errores de formato y mantengan coherencia temporal con respecto a la duración del video:

```bash
./main.py validar
```

---

## 🛠️ Resumen de Comandos de `./main.py`

| Comando | Descripción | Ejemplo |
|---|---|---|
| `crear` | Crea el esqueleto para una nueva sesión | `./main.py crear S002` |
| `procesar` | Normaliza el video original y extrae el audio | `./main.py procesar S002` |
| `extraer-frames` | Extrae 1 fotograma por segundo | `./main.py extraer-frames S002` |
| `extraer-features`| Extrae energía RMS, ZCR y densidad de movimiento | `./main.py extraer-features S002` |
| `pipeline` | Ejecuta `procesar` + `frames` + `features` en cadena | `./main.py pipeline S002` |
| `exportar` | Exporta la línea temporal a TSV (compatible con ELAN) | `./main.py exportar S002` |
| `validar` | Valida esquemas, tiempos y consistencia del dataset | `./main.py validar` |
| `analizar` | Resume cobertura, features y preparación para entrenamiento | `./main.py analizar` |
| `preparar-anotacion` | Genera una cola de ventanas priorizadas para revisión humana | `./main.py preparar-anotacion S001` |
| `preanotar` | Genera candidatos de señales para revisión experta, sin crear ground truth | `./main.py preanotar S001` |

El anotador local muestra la cola de revisión como navegación de solo lectura:
seleccionar una tarea busca el inicio de su ventana y carga sus límites en el
formulario. No cambia el estado de la tarea; la revisión y adjudicación siguen
siendo responsabilidad humana. Cuando hay preanotaciones disponibles, se muestran
separadas como referencias automáticas no validadas; no se copian a los eventos ni
se convierten en ground truth. Los eventos canónicos que conservan un campo `source`
también se identifican como propuestas y quedan en solo lectura para evitar que
una edición descarte accidentalmente su procedencia. Las colas nuevas parten con la
guía `draft-0.1` y `guide_status=pending`; el exportador de ventanas revisadas exige
un estado aprobado y quién/cuándo lo aprobó. La interfaz muestra cuántas tareas
tienen esa evidencia registrada, sin ofrecer controles para aprobar la guía.

Antes de registrar una versión de guía como aprobada, el equipo puede revisar su
completitud estructural con:

```bash
python scripts/validar_guia_anotacion.py --guide path/to/approved-guide.md
```

El comando sobre la plantilla incluida debe fallar mientras queden campos pendientes.
Un resultado válido sólo confirma campos completos y aprobación registrada; no
certifica que los criterios sean clínicamente correctos.

### Alcance y verificación

Las sesiones de integración se conservan localmente, pero están declaradas en
`config/dataset.yaml` como excluidas del dataset productivo. La validación y el
análisis reportan esas exclusiones sin borrarlas.

Para ejecutar todos los tests desde la raíz del repositorio:

```bash
python -m unittest discover -s . -p 'test_*.py'
```

El análisis estructural no autoriza entrenamiento. Antes de entrenar todavía se
requieren revisión clínica, acuerdo independiente, consentimiento verificable y
particiones por paciente.
| `anotar` | Abre el video y permite crear, editar y borrar anotaciones | `./main.py anotar` |

La validación comprueba integridad de archivos y vocabularios. El análisis distingue
además las anotaciones reales de las marcadas con `"es_ejemplo": true`; una sesión
solo se considera lista para entrenamiento cuando terminó el pipeline y posee al
menos una anotación real.

---

## 📂 Estructura de cada Sesión

```text
dataset/sessions/S001/
├── metadata/
│   └── session.json           # Participantes, calidad y estado del pipeline
├── raw/                       # Grabación original sin alterar
├── processed/
│   ├── audio/                 # Audio estandarizado (16kHz mono .wav)
│   ├── video/                 # Video normalizado (1280x720, 10fps .mp4)
│   ├── frames/                # Frames a 1 fps (.jpg)
│   └── features/              # audio_features.json y visual_motion.json
└── annotations/
    ├── visual/events.json
    ├── audio/events.json
    ├── interaction/events.json
    └── demuca/evaluations.json
```
