#!/usr/bin/env python3
"""
Script para convertir o exportar anotaciones entre formato JSON del dataset DEMUCA
y formatos estándar de investigación como ELAN (.eaf).
"""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def exportar_a_elan_tsv(session_dir: Path, output_file: Path):
    """
    Genera un archivo TSV compatible con la importación de ELAN / Audacity / Praat
    combinando todas las modalidades anotadas.
    """
    filas = ["start_time\tend_time\ttier\tvalue\tparticipant_or_speaker"]
    
    # 1. Eventos visuales, audio, interaccion
    for mod in ("visual", "audio", "interaction"):
        p = session_dir / "annotations" / mod / "events.json"
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for ev in data.get("events", []):
                s = ev.get("start_seconds", 0)
                e = ev.get("end_seconds", 0)
                t = ev.get("type", "")
                who = ev.get("participant") or ev.get("speaker") or ",".join(ev.get("participants", []))
                filas.append(f"{s:.3f}\t{e:.3f}\t{mod.upper()}\t{t}\t{who}")
        except Exception as err:
            print(f"[WARN] Error leyendo {p}: {err}")

    # 2. DEMUCA
    demuca_p = session_dir / "annotations" / "demuca" / "evaluations.json"
    if demuca_p.exists():
        try:
            data = json.loads(demuca_p.read_text(encoding="utf-8"))
            for eval_item in data.get("evaluations", []):
                for resp in eval_item.get("responses", []):
                    subscale = resp.get("subscale", "")
                    score = resp.get("score", "")
                    for ev in resp.get("evidence", []):
                        s = ev.get("start_seconds", 0)
                        e = ev.get("end_seconds", 0)
                        desc = ev.get("description", "").replace("\t", " ")
                        filas.append(f"{s:.3f}\t{e:.3f}\tDEMUCA_{subscale}\tScore:{score} - {desc}\tP001")
        except Exception as err:
            print(f"[WARN] Error leyendo DEMUCA: {err}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(filas) + "\n", encoding="utf-8")
    print(f"[OK] Exportado TSV compatible con ELAN/anotadores en: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Exportador de anotaciones a TSV/ELAN")
    parser.add_argument("session_id", help="ID de la sesión (ej. S001)")
    parser.add_argument(
        "--raiz",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Directorio raíz del dataset"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Ruta del archivo de salida (opcional)"
    )
    args = parser.parse_args()

    session_dir = args.raiz / "dataset" / "sessions" / args.session_id
    if not session_dir.exists():
        print(f"[ERROR] No existe la sesión: {session_dir}")
        return

    out_file = args.out or (session_dir / "annotations" / f"{args.session_id}_timeline.tsv")
    exportar_a_elan_tsv(session_dir, out_file)


if __name__ == "__main__":
    main()
