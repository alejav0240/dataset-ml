import tempfile
import unittest
from pathlib import Path

from scripts.validar_guia_anotacion import validate_guide


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASK_CONFIG = PROJECT_ROOT / "ml" / "task.json"
TEMPLATE = PROJECT_ROOT / "dataset" / "GUIA_ANOTACION_TEMPLATE.md"


class ValidateGuideTests(unittest.TestCase):
    def test_unapproved_template_is_blocked_without_mutation(self):
        original = TEMPLATE.read_text(encoding="utf-8")

        report = validate_guide(TEMPLATE, TASK_CONFIG)

        self.assertFalse(report["valid"])
        self.assertEqual(report["labels_checked"], 20)
        self.assertIn("guide_not_explicitly_approved", report["blockers"])
        self.assertIn("guide_has_pending_fields", report["blockers"])
        self.assertEqual(TEMPLATE.read_text(encoding="utf-8"), original)

    def test_completed_guide_copy_passes_structural_preflight(self):
        guide = TEMPLATE.read_text(encoding="utf-8")
        guide = guide.replace("Estado de guía: BORRADOR", "Estado de guía: APROBADA", 1)
        guide = guide.replace("PENDIENTE", "Completado y aprobado por el equipo")
        guide = guide.replace("- [ ] ", "- [x] ")

        with tempfile.TemporaryDirectory() as temp_dir:
            completed_copy = Path(temp_dir) / "annotation-guide-v1.md"
            completed_copy.write_text(guide, encoding="utf-8")

            report = validate_guide(completed_copy, TASK_CONFIG)

        self.assertTrue(report["valid"], report["blockers"])
        self.assertEqual(report["labels_checked"], 20)
        self.assertIn("does not approve clinical criteria", report["notice"])

    def test_rejects_missing_label_definition(self):
        guide = TEMPLATE.read_text(encoding="utf-8").replace(
            "#### `MOVIMIENTO` — Movimiento corporal observable",
            "#### `UNKNOWN_LABEL` — Unknown",
            1,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            guide_copy = Path(temp_dir) / "guide.md"
            guide_copy.write_text(guide, encoding="utf-8")
            report = validate_guide(guide_copy, TASK_CONFIG)

        self.assertIn("label_definition_missing:MOVIMIENTO", report["blockers"])
        self.assertIn("unknown_label_definition:UNKNOWN_LABEL", report["blockers"])

    def test_rejects_blank_or_removed_label_rule(self):
        completed = TEMPLATE.read_text(encoding="utf-8")
        completed = completed.replace("Estado de guía: BORRADOR", "Estado de guía: APROBADA", 1)
        completed = completed.replace("PENDIENTE", "Criterio definido por el equipo")
        completed = completed.replace("- [ ] ", "- [x] ")
        original_rule = "- Regla operativa aprobada: `Criterio definido por el equipo`"

        with tempfile.TemporaryDirectory() as temp_dir:
            guide_path = Path(temp_dir) / "guide.md"
            for replacement, expected in (
                ("- Regla operativa aprobada: ", "label_field_incomplete:MOVIMIENTO:operational_rule"),
                ("", "label_field_missing:MOVIMIENTO:operational_rule"),
            ):
                guide_path.write_text(completed.replace(original_rule, replacement, 1), encoding="utf-8")
                report = validate_guide(guide_path, TASK_CONFIG)
                self.assertIn(expected, report["blockers"])


if __name__ == "__main__":
    unittest.main()
