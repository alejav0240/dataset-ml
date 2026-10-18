import csv
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from preparar_anotacion import prepare


class PrepareAnnotationTests(unittest.TestCase):
    def test_annotation_guide_template_covers_task_labels(self):
        project_root = Path(__file__).resolve().parents[2]
        task = json.loads((project_root / "ml" / "task.json").read_text(encoding="utf-8"))
        template = (project_root / "dataset" / "GUIA_ANOTACION_TEMPLATE.md").read_text(
            encoding="utf-8"
        )
        required_labels = {
            label
            for modality_labels in task["label_sources"].values()
            for label in modality_labels
        }
        template_labels = set(re.findall(r"#### `([^`]+)`", template))

        self.assertEqual(template_labels, required_labels)

    def test_new_review_queue_starts_with_unapproved_guide(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            session = root / "dataset" / "sessions" / "S001"
            (session / "metadata").mkdir(parents=True)
            features = session / "processed" / "features"
            features.mkdir(parents=True)
            (session / "metadata" / "session.json").write_text(
                json.dumps({"technical": {"duration_seconds": 5}}),
                encoding="utf-8",
            )
            (features / "audio_features.json").write_text(
                json.dumps({"timestamps": [1], "rms_energy": [0.1], "zero_crossing_rate": [0.2]}),
                encoding="utf-8",
            )
            (features / "visual_motion.json").write_text(
                json.dumps({"timestamps": [1], "motion_intensity": [0.3]}),
                encoding="utf-8",
            )
            output = root / "review" / "annotation_tasks.tsv"

            with patch("preparar_anotacion.ROOT", root):
                prepare("S001", 5, output, overwrite=False)

            with output.open(encoding="utf-8", newline="") as file:
                row = next(csv.DictReader(file, delimiter="\t"))

        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["guide_version"], "draft-0.1")
        self.assertEqual(row["guide_status"], "pending")
        self.assertEqual(row["guide_approved_by"], "")
        self.assertEqual(row["guide_approved_at"], "")


if __name__ == "__main__":
    unittest.main()
