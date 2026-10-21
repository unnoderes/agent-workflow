"""Tests for pairing frames with cue durations and writing the manifest."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_concat_list import (  # noqa: E402
    ConcatError,
    build_plan,
    generate_concat_list,
    list_frame_files,
    main,
)

SRT_THREE_CUES = """1
00:00:00,000 --> 00:00:01,000
A

2
00:00:01,000 --> 00:00:03,000
B

3
00:00:03,000 --> 00:00:09,000
C
"""


class ConcatPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.frames_dir = self.tmp / "画面"
        self.frames_dir.mkdir()

    def add_frames(self, count: int) -> None:
        for index in range(1, count + 1):
            (self.frames_dir / f"frame_{index:02d}.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    def write_srt(self, text: str = SRT_THREE_CUES) -> Path:
        path = self.tmp / "subtitles.srt"
        path.write_text(text, encoding="utf-8")
        return path

    def test_pairs_frames_with_cue_durations_in_order(self) -> None:
        self.add_frames(3)

        plan = build_plan(
            self.write_srt(), self.frames_dir, self.tmp / "concat_list.txt"
        )

        self.assertEqual(
            [entry.duration_ms for entry in plan.entries], [1000, 2000, 6000]
        )
        self.assertEqual(plan.total_duration_ms, 9000)
        self.assertEqual(
            [entry.frame.name for entry in plan.entries],
            ["frame_01.png", "frame_02.png", "frame_03.png"],
        )

    def test_orders_frames_numerically_not_lexically(self) -> None:
        self.add_frames(10)

        frames = list_frame_files(self.frames_dir)

        self.assertEqual(frames[1].name, "frame_02.png")
        self.assertEqual(frames[-1].name, "frame_10.png")

    def test_ignores_files_that_are_not_numbered_frames(self) -> None:
        self.add_frames(3)
        (self.frames_dir / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (self.frames_dir / "notes.txt").write_text("x", encoding="utf-8")

        frames = list_frame_files(self.frames_dir)

        self.assertEqual([frame.name for frame in frames], ["frame_01.png", "frame_02.png", "frame_03.png"])

    def test_rejects_frame_count_mismatch(self) -> None:
        self.add_frames(4)

        with self.assertRaises(ConcatError) as ctx:
            build_plan(self.write_srt(), self.frames_dir, self.tmp / "concat_list.txt")

        message = str(ctx.exception)
        self.assertIn("4 个 PNG 帧 vs 3 段字幕", message)
        self.assertIn("html-image-export", message)

    def test_rejects_empty_frames_dir(self) -> None:
        with self.assertRaises(ConcatError) as ctx:
            build_plan(self.write_srt(), self.frames_dir, self.tmp / "concat_list.txt")

        self.assertIn("没有 frame_*.png", str(ctx.exception))

    def test_rejects_missing_frames_dir(self) -> None:
        with self.assertRaises(ConcatError) as ctx:
            build_plan(
                self.write_srt(), self.tmp / "缺失目录", self.tmp / "concat_list.txt"
            )

        self.assertIn("找不到画面目录", str(ctx.exception))

    def test_reports_srt_problems_as_concat_errors(self) -> None:
        self.add_frames(3)

        with self.assertRaises(ConcatError) as ctx:
            build_plan(
                self.write_srt("1\nnot a timestamp\n"),
                self.frames_dir,
                self.tmp / "concat_list.txt",
            )

        self.assertIn("不是合法的 SRT 时间戳", str(ctx.exception))

    def test_extends_last_frame_to_cover_longer_audio(self) -> None:
        self.add_frames(3)

        plan = build_plan(
            self.write_srt(),
            self.frames_dir,
            self.tmp / "concat_list.txt",
            pad_to_sec=9.5,
        )

        self.assertEqual(plan.total_duration_ms, 9500)
        self.assertEqual(plan.entries[-1].duration_ms, 6500)
        self.assertIn("最后一帧已延长至音频结尾", "\n".join(plan.warnings))

    def test_warns_when_subtitles_outlast_the_audio(self) -> None:
        self.add_frames(3)

        plan = build_plan(
            self.write_srt(),
            self.frames_dir,
            self.tmp / "concat_list.txt",
            pad_to_sec=8.0,
        )

        self.assertEqual(plan.total_duration_ms, 9000)
        self.assertIn("会被裁剪到音频长度", "\n".join(plan.warnings))

    def test_no_padding_warning_when_audio_matches(self) -> None:
        self.add_frames(3)

        plan = build_plan(
            self.write_srt(),
            self.frames_dir,
            self.tmp / "concat_list.txt",
            pad_to_sec=9.0,
        )

        self.assertEqual(plan.warnings, [])


class ManifestRenderingTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.frames_dir = self.tmp / "画面"
        self.frames_dir.mkdir()
        for index in range(1, 4):
            (self.frames_dir / f"frame_{index:02d}.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        self.srt = self.tmp / "subtitles.srt"
        self.srt.write_text(SRT_THREE_CUES, encoding="utf-8")

    def test_manifest_lists_every_frame_then_repeats_the_last(self) -> None:
        plan = generate_concat_list(
            self.srt, self.frames_dir, self.tmp / "concat_list.txt"
        )

        lines = plan.output_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(
            lines,
            [
                "file '画面/frame_01.png'",
                "duration 1.000",
                "file '画面/frame_02.png'",
                "duration 2.000",
                "file '画面/frame_03.png'",
                "duration 6.000",
                "file '画面/frame_03.png'",
            ],
        )

    def test_manifest_uses_paths_relative_to_its_own_directory(self) -> None:
        plan = generate_concat_list(
            self.srt, self.frames_dir, self.tmp / "build" / "concat_list.txt"
        )

        content = plan.output_path.read_text(encoding="utf-8")

        self.assertIn("file '../画面/frame_01.png'", content)


class ManifestPathEscapingTest(unittest.TestCase):
    def test_quotes_and_forward_slashes_survive_spaces_and_apostrophes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frames_dir = Path(tmp) / "my 画面's"
            frames_dir.mkdir()
            (frames_dir / "frame_01.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            srt = Path(tmp) / "subs.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nA\n", encoding="utf-8")

            plan = generate_concat_list(srt, frames_dir, Path(tmp) / "concat_list.txt")

            first_line = plan.output_path.read_text(encoding="utf-8").splitlines()[0]

            self.assertEqual(first_line, "file 'my 画面'\\''s/frame_01.png'")
            self.assertNotIn("\\", first_line.replace("'\\''", ""))


class ConcatCliTest(unittest.TestCase):
    def test_cli_writes_manifest_and_reports_totals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            frames_dir = tmp_path / "画面"
            frames_dir.mkdir()
            for index in range(1, 4):
                (frames_dir / f"frame_{index:02d}.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            srt = tmp_path / "subtitles.srt"
            srt.write_text(SRT_THREE_CUES, encoding="utf-8")
            manifest = tmp_path / "concat_list.txt"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main([str(srt), str(frames_dir), str(manifest), "--pad-to", "9.5"])

            self.assertEqual(code, 0)
            self.assertTrue(manifest.is_file())
            self.assertIn("总时长：9.500s", stdout.getvalue())

    def test_cli_exits_1_on_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            frames_dir = tmp_path / "画面"
            frames_dir.mkdir()
            (frames_dir / "frame_01.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            srt = tmp_path / "subtitles.srt"
            srt.write_text(SRT_THREE_CUES, encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main([str(srt), str(frames_dir), str(tmp_path / "cl.txt")])

            self.assertEqual(code, 1)
            self.assertIn("[ERROR]", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
