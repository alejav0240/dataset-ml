#!/usr/bin/env python3
"""
CLI centralizado para la gestión del dataset DEMUCA.
Permite ejecutar todos los pasos del pipeline con comandos simples:

  ./main.py crear S002
  ./main.py procesar S002
  ./main.py extraer-frames S002
  ./main.py extraer-features S002
  ./main.py pipeline S002         (ejecuta procesar + frames + features)
  ./main.py exportar S002
  ./main.py validar
  ./main.py analizar
  ./main.py preparar-anotacion S001
  ./main.py anotar
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
PYTHON_BIN = ROOT / ".venv" / "bin" / "python"
if not PYTHON_BIN.exists():
    PYTHON_BIN = Path(sys.executable)


def ejecutar_script(script_name: str, args: list[str]) -> int:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"[ERROR] Script no encontrado: {script_path}", file=sys.stderr)
        return 1
    cmd = [str(PYTHON_BIN), str(script_path)] + args
    res = subprocess.run(cmd)
    return res.returncode


# ============================================================
# Comandos
# ============================================================

def cmd_crear(session_id: str, force: bool = False):
    """Crea la estructura de carpetas, esquemas y metadatos base para una nueva sesión."""
    session_dir = ROOT / "dataset" / "sessions" / session_id
    if session_dir.exists() and not force:
        print(f"[AVISO] La sesión {session_id} ya existe en {session_dir}. Usa --force para sobrescribir.")
        return

    # Usar crear_estructura_dataset
    cmd = [str(PYTHON_BIN), str(ROOT / "crear_estructura_dataset.py"), "--session", session_id]
    if force:
        cmd.append("--force")
    subprocess.run(cmd)


def cmd_procesar(session_id: str, sobrescribir: bool = False):
    """Normaliza audio (16kHz mono) y video (1280x720 10fps)."""
    args = [session_id]
    if sobrescribir:
        args.append("--sobrescribir")
    return ejecutar_script("procesar_sesion.py", args)


def cmd_extraer_frames(session_id: str, sobrescribir: bool = False):
    """Extrae 1 frame por segundo del video normalizado."""
    args = [session_id]
    if sobrescribir:
        args.append("--sobrescribir")
    code = ejecutar_script("extraer_frames.py", args)
    
    # Asegurar actualización de flag en metadata
    metadata_path = ROOT / "dataset" / "sessions" / session_id / "metadata" / "session.json"
    if code == 0 and metadata_path.exists():
        try:
            meta = json.loads(metadata_path.read_text(encoding="utf-8"))
            meta.setdefault("processing", {})["frames_extracted"] = True
            metadata_path.write_text(json.dumps(meta, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            pass
    return code


def cmd_extraer_features(session_id: str, sobrescribir: bool = False):
    """Calcula características acústicas (RMS, ZCR) y visuales (densidad de movimiento)."""
    args = [session_id]
    if sobrescribir:
        args.append("--sobrescribir")
    return ejecutar_script("extraer_features.py", args)


def cmd_pipeline(session_id: str, sobrescribir: bool = False):
    """Ejecuta en cadena: procesar -> extraer-frames -> extraer-features."""
    print(f"\n=== [1/3] Normalizando medios para {session_id} ===")
    code = cmd_procesar(session_id, sobrescribir)
    if code != 0:
        print(f"[FALLO] Falló la normalización para {session_id}")
        return code

    print(f"\n=== [2/3] Extrayendo frames para {session_id} ===")
    code = cmd_extraer_frames(session_id, sobrescribir)
    if code != 0:
        print(f"[FALLO] Falló la extracción de frames para {session_id}")
        return code

    print(f"\n=== [3/3] Extrayendo features para {session_id} ===")
    code = cmd_extraer_features(session_id, sobrescribir)
    if code != 0:
        print(f"[FALLO] Falló la extracción de features para {session_id}")
        return code

    print(f"\n=== [COMPLETADO] Pipeline finalizado con éxito para {session_id} ===")
    return 0


def cmd_exportar(session_id: str, out: str | None = None):
    """Exporta anotaciones a TSV compatible con ELAN/etiquetadores."""
    args = [session_id]
    if out:
        args.extend(["--out", out])
    return ejecutar_script("exportar_anotaciones.py", args)


def cmd_validar():
    """Valida la integridad de todas las sesiones del dataset."""
    return ejecutar_script("validar_dataset.py", [])


def cmd_analizar(json_output: bool = False, out: str | None = None):
    """Resume cobertura, estadísticas y preparación para entrenamiento."""
    args = []
    if json_output:
        args.append("--json")
    if out:
        args.extend(["--out", out])
    return ejecutar_script("analizar_dataset.py", args)


def cmd_preparar_anotacion(session_id: str, ventana: float, out: str | None, sobrescribir: bool):
    """Crea una cola temporal priorizada para anotación humana."""
    args = [session_id, "--ventana", str(ventana)]
    if out:
        args.extend(["--out", out])
    if sobrescribir:
        args.append("--sobrescribir")
    return ejecutar_script("preparar_anotacion.py", args)


def cmd_preanotar(session_id: str, out: str | None, sobrescribir: bool):
    """Genera candidatos derivados de señales para revisión experta."""
    args = [session_id]
    if out:
        args.extend(["--out", out])
    if sobrescribir:
        args.append("--sobrescribir")
    return ejecutar_script("generar_preanotaciones.py", args)


def cmd_anotar(host: str, port: int, no_browser: bool):
    """Inicia la herramienta audiovisual local de anotación."""
    args = ["--host", host, "--port", str(port)]
    if no_browser:
        args.append("--no-browser")
    tool_path = ROOT / "tools" / "anotador.py"
    try:
        return subprocess.run([str(PYTHON_BIN), str(tool_path), *args]).returncode
    except KeyboardInterrupt:
        return 0


# ============================================================
# Entrypoint CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="DEMUCA Dataset CLI: Gestor de pipeline multimodal",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Comando a ejecutar")

    # crear
    p_crear = subparsers.add_parser("crear", help="Crea la estructura para una nueva sesión")
    p_crear.add_argument("session_id", help="Identificador (ej. S002)")
    p_crear.add_argument("--force", action="store_true", help="Sobrescribir si ya existe")

    # procesar
    p_proc = subparsers.add_parser("procesar", help="Normaliza video y audio")
    p_proc.add_argument("session_id", help="Identificador (ej. S002)")
    p_proc.add_argument("--sobrescribir", action="store_true", help="Regenerar")

    # extraer-frames
    p_frames = subparsers.add_parser("extraer-frames", help="Extrae frames a 1 fps")
    p_frames.add_argument("session_id", help="Identificador (ej. S002)")
    p_frames.add_argument("--sobrescribir", action="store_true", help="Regenerar")

    # extraer-features
    p_feat = subparsers.add_parser("extraer-features", help="Calcula features de audio y densidad de movimiento")
    p_feat.add_argument("session_id", help="Identificador (ej. S002)")
    p_feat.add_argument("--sobrescribir", action="store_true", help="Regenerar")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Ejecuta procesar + extraer-frames + extraer-features")
    p_pipe.add_argument("session_id", help="Identificador (ej. S002)")
    p_pipe.add_argument("--sobrescribir", action="store_true", help="Regenerar")

    # exportar
    p_exp = subparsers.add_parser("exportar", help="Exporta a TSV compatible con ELAN")
    p_exp.add_argument("session_id", help="Identificador (ej. S002)")
    p_exp.add_argument("--out", help="Ruta del archivo de salida")

    # validar
    subparsers.add_parser("validar", help="Valida todas las sesiones del dataset")

    # analizar
    p_analysis = subparsers.add_parser("analizar", help="Analiza cobertura y preparación para entrenamiento")
    p_analysis.add_argument("--json", action="store_true", help="Mostrar informe JSON")
    p_analysis.add_argument("--out", help="Guardar informe JSON")

    p_prepare = subparsers.add_parser(
        "preparar-anotacion", help="Genera ventanas priorizadas para revisión humana"
    )
    p_prepare.add_argument("session_id", help="Identificador (ej. S001)")
    p_prepare.add_argument("--ventana", type=float, default=30.0, help="Duración en segundos")
    p_prepare.add_argument("--out", help="Ruta TSV de salida")
    p_prepare.add_argument("--sobrescribir", action="store_true", help="Regenerar la cola")

    p_preannotate = subparsers.add_parser(
        "preanotar", help="Genera candidatos de señales para revisión experta"
    )
    p_preannotate.add_argument("session_id", help="Identificador (ej. S001)")
    p_preannotate.add_argument("--out", help="Ruta JSON de salida")
    p_preannotate.add_argument("--sobrescribir", action="store_true", help="Regenerar candidatos")

    p_annotate = subparsers.add_parser("anotar", help="Abre el anotador audiovisual local")
    p_annotate.add_argument("--host", default="127.0.0.1", help="Host local")
    p_annotate.add_argument("--port", type=int, default=8765, help="Puerto local")
    p_annotate.add_argument("--no-browser", action="store_true", help="No abrir navegador")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    if args.subcommand == "crear":
        cmd_crear(args.session_id, args.force)
    elif args.subcommand == "procesar":
        sys.exit(cmd_procesar(args.session_id, args.sobrescribir))
    elif args.subcommand == "extraer-frames":
        sys.exit(cmd_extraer_frames(args.session_id, args.sobrescribir))
    elif args.subcommand == "extraer-features":
        sys.exit(cmd_extraer_features(args.session_id, args.sobrescribir))
    elif args.subcommand == "pipeline":
        sys.exit(cmd_pipeline(args.session_id, args.sobrescribir))
    elif args.subcommand == "exportar":
        sys.exit(cmd_exportar(args.session_id, args.out))
    elif args.subcommand == "validar":
        sys.exit(cmd_validar())
    elif args.subcommand == "analizar":
        sys.exit(cmd_analizar(args.json, args.out))
    elif args.subcommand == "preparar-anotacion":
        sys.exit(cmd_preparar_anotacion(
            args.session_id, args.ventana, args.out, args.sobrescribir
        ))
    elif args.subcommand == "preanotar":
        sys.exit(cmd_preanotar(args.session_id, args.out, args.sobrescribir))
    elif args.subcommand == "anotar":
        sys.exit(cmd_anotar(args.host, args.port, args.no_browser))


if __name__ == "__main__":
    main()
