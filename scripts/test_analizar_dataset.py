import json
import tempfile
import unittest
from pathlib import Path

from scripts.analizar_dataset import analyze_dataset, analyze_session


class AnalyzeDatasetTests(unittest.TestCase):
    def test_processing_and_annotations_do_not_imply_training_authorization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session = Path(temp_dir) / "S001"
            (session / "metadata").mkdir(parents=True)
            (session / "annotations" / "visual").mkdir(parents=True)
            (session / "metadata" / "session.json").write_text(
                json.dumps({
                    "technical": {"duration_seconds": 10},
                    "processing": {
                        "video_processed": True,
                        "audio_processed": True,
                        "frames_extracted": True,
                        "features_extracted": True,
                    },
                }),
                encoding="utf-8",
            )
            (session / "annotations" / "visual" / "events.json").write_text(
                json.dumps({"events": [{"type": "MOVIMIENTO", "es_ejemplo": False}]}),
                encoding="utf-8",
            )

            report = analyze_session(session)

        self.assertTrue(report["annotation_candidate_ready"])
        self.assertFalse(report["training_ready"])

    def test_dataset_summary_labels_candidates_not_training_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            session = root / "S001"
            (session / "metadata").mkdir(parents=True)
            (session / "metadata" / "session.json").write_text(
                json.dumps({"technical": {"duration_seconds": 1}}), encoding="utf-8"
            )
            import scripts.analizar_dataset as analizar_dataset

            original_sessions_dir = analizar_dataset.SESSIONS_DIR
            analizar_dataset.SESSIONS_DIR = root
            try:
                report = analyze_dataset()
            finally:
                analizar_dataset.SESSIONS_DIR = original_sessions_dir

        self.assertEqual(report["sessions_annotation_candidate_ready"], 0)
        self.assertEqual(report["sessions_training_ready"], 0)
        self.assertFalse(report["training_readiness_assessed"])


if __name__ == "__main__":
    unittest.main()
