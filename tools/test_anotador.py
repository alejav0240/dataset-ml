import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.anotador import preview_video_for, read_pose_landmarks, read_review_candidates, read_review_tasks


class ReviewTaskTests(unittest.TestCase):
    def test_preview_video_uses_existing_video_when_audio_is_already_present(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sessions = Path(temp_dir)
            video = sessions / "S001" / "processed" / "video" / "input.mp4"
            video.parent.mkdir(parents=True)
            video.write_bytes(b"video")
            with patch("tools.anotador.SESSIONS_DIR", sessions), patch("tools.anotador._has_audio_stream", return_value=True):
                self.assertEqual(preview_video_for("S001"), video)

    def test_reads_review_queue_without_changing_task_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sessions = Path(temp_dir)
            queue = sessions / "S001" / "annotations" / "review" / "annotation_tasks.tsv"
            queue.parent.mkdir(parents=True)
            with queue.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=("task_id", "start_seconds", "end_seconds", "status"),
                    delimiter="\t",
                )
                writer.writeheader()
                writer.writerow({
                    "task_id": "S001-W0001",
                    "start_seconds": "0.0",
                    "end_seconds": "30.0",
                    "status": "needs_clinical_review",
                })

            with patch("tools.anotador.SESSIONS_DIR", sessions):
                tasks = read_review_tasks("S001")

            self.assertEqual(tasks[0]["task_id"], "S001-W0001")
            self.assertEqual(tasks[0]["status"], "needs_clinical_review")
            self.assertEqual(queue.read_text(encoding="utf-8").count("needs_clinical_review"), 1)

    def test_missing_queue_is_an_empty_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sessions = Path(temp_dir)
            (sessions / "S001").mkdir()
            with patch("tools.anotador.SESSIONS_DIR", sessions):
                self.assertEqual(read_review_tasks("S001"), [])

    def test_candidates_are_read_only_references_for_a_known_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sessions = Path(temp_dir)
            base = sessions / "S001" / "annotations"
            review = base / "review"
            preannotations = base / "preannotations"
            review.mkdir(parents=True)
            preannotations.mkdir(parents=True)
            (review / "annotation_tasks.tsv").write_text(
                "task_id\tstart_seconds\tend_seconds\tstatus\n"
                "S001-W0001\t0\t30\tneeds_clinical_review\n",
                encoding="utf-8",
            )
            (preannotations / "v1_signal_candidates.json").write_text(
                '{"ground_truth": false, "candidates": [{"candidate_id": "S001-W0001", "signals": {"audio_activity": {"level": "ALTA"}}}]}',
                encoding="utf-8",
            )
            (preannotations / "v1_visual_observations.json").write_text(
                '{"observations": [{"candidate_id": "S001-W0001", "visible_observations": [{"evidence": "review only"}]}]}',
                encoding="utf-8",
            )

            with patch("tools.anotador.SESSIONS_DIR", sessions):
                candidates = read_review_candidates("S001", "S001-W0001")
                with self.assertRaisesRegex(ValueError, "no existe"):
                    read_review_candidates("S001", "S001-W0002")

            self.assertFalse(candidates["ground_truth"])
            self.assertTrue(candidates["review_required"])
            self.assertEqual(candidates["signal_candidate"]["signals"]["audio_activity"]["level"], "ALTA")
            self.assertEqual(candidates["visual_observations"][0]["evidence"], "review only")
            self.assertEqual(
                (review / "annotation_tasks.tsv").read_text(encoding="utf-8").splitlines()[-1].split("\t")[-1],
                "needs_clinical_review",
            )

    def test_pose_overlay_payload_is_read_only_and_keeps_pose_indices(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sessions = Path(temp_dir)
            pose_path = sessions / "S001" / "processed" / "features" / "pose_landmarks.json"
            pose_path.parent.mkdir(parents=True)
            pose_path.write_text(
                '{"session_id":"S001","sampling_fps":1,"landmark_count_per_pose":33,'
                '"frames":[{"timestamp_seconds":0,"poses":[{"pose_index":0,"landmarks":[]}]}]}',
                encoding="utf-8",
            )
            with patch("tools.anotador.SESSIONS_DIR", sessions):
                payload = read_pose_landmarks("S001")
            self.assertTrue(payload["available"])
            self.assertEqual(payload["frames"][0]["poses"][0]["pose_index"], 0)

    def test_missing_pose_overlay_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sessions = Path(temp_dir)
            (sessions / "S001").mkdir()
            with patch("tools.anotador.SESSIONS_DIR", sessions):
                payload = read_pose_landmarks("S001")
            self.assertFalse(payload["available"])


if __name__ == "__main__":
    unittest.main()
