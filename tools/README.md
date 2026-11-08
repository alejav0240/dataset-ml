# Anotador audiovisual DEMUCA

Herramienta local para reproducir una sesión y crear, editar o eliminar eventos
visuales, de audio y de interacción usando el vocabulario válido del dataset.

## Inicio

```bash
cd /home/javi/Proyectos/cbm-front/dataset
./main.py anotar
```

Se abrirá `http://127.0.0.1:8765`. Si el navegador no se abre:

```bash
./main.py anotar --no-browser
```

## Flujo de trabajo

1. Seleccionar sesión y modalidad.
2. Seleccionar el paciente y el terapeuta en el encabezado.
3. Reproducir el video hasta el inicio del evento.
4. Presionar `I` o **Usar tiempo como inicio**.
5. Avanzar hasta el final y presionar `O` o **Usar tiempo como fin**.
6. Elegir tipo, actor y atributos.
7. Guardar el evento.
8. Ejecutar `./main.py validar` al terminar un lote.

Cuando la sesión tiene `processed/features/pose_landmarks.json`, el anotador
dibuja los 33 landmarks de cada pose detectada sobre el video y los conecta
con líneas. El color identifica el índice de pose de MediaPipe. La selección
de paciente y terapeuta asigna actores a los formularios, pero no identifica
automáticamente qué índice de pose corresponde a cada persona.

### Anotación simultánea

Marca un único inicio y fin, activa Visual, Audio e Interacción, completa el tipo y
los atributos de cada tarjeta y pulsa **Guardar modalidades seleccionadas**. El
servidor valida todo el lote antes de escribir; también puedes activar solo dos de
las tres modalidades.

La barra espaciadora pausa/reanuda. Los botones permiten saltar ±1 o ±5 segundos.
Al pulsar el tiempo de un evento guardado, el video salta a su inicio.

## Persistencia y seguridad

- La aplicación escucha únicamente en `127.0.0.1` de forma predeterminada.
- Escribe en `annotations/{visual,audio,interaction}/events.json`.
- Antes de modificar un archivo conserva la versión anterior como `events.json.bak`.
- La escritura es atómica para reducir el riesgo de archivos incompletos.
- El servidor rechaza tipos, atributos, actores y tiempos no permitidos.
- No expone rutas arbitrarias del equipo.

No usar `--host 0.0.0.0` en una red compartida: la herramienta no implementa
autenticación porque está diseñada para uso local.
