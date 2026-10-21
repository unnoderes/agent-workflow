"""Tests for SRT parsing, the source of every frame duration."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse_srt_durations import (  # noqa: E402
    SrtError,
    main,
    ms_to_srt_time,
    parse_srt,
    parse_srt_durations,
    validate_timeline,
)

BASIC_SRT = """1
00:00:00,000 --> 00:00:03,000
第一段字幕

2
00:00:03,000 --> 00:00:06,000
第二段字幕

3
00:00:06,000 --> 00:00:09,000
第三段字幕
"""


class ParseSrtTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write_srt(self, text: str, name: str = "subtitles.srt") -> Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_parses_cues_with_durations_and_text(self) -> None:
        cues = parse_srt(self.write_srt(BASIC_SRT))

        self.assertEqual([cue.index for cue in cues], [1, 2, 3])
        self.assertEqual([cue.duration_ms for cue in cues], [3000, 3000, 3000])
        self.assertEqual(cues[0].start_ms, 0)
        self.assertEqual(cues[0].text, "第一段字幕")
        self.assertEqual(parse_srt_durations(self.tmp / "subtitles.srt"), [3.0, 3.0, 3.0])

    def test_accepts_bom_crlf_and_dot_milliseconds(self) -> None:
        text = BASIC_SRT.replace("\n", "\r\n").replace(",000", ".000")
        path = self.tmp / "bom.srt"
        path.write_bytes(text.encode("utf-8-sig"))

        cues = parse_srt(path)

        self.assertEqual(len(cues), 3)
        self.assertEqual(cues[-1].end_ms, 9000)

    def test_fraction_digits_are_ms_not_fractions_of_a_second(self) -> None:
        text = "1\n00:00:00,5 --> 00:00:01,45\n短\n"
        cues = parse_srt(self.write_srt(text))

        self.assertEqual(cues[0].duration_ms, 950)

    def test_tolerates_blank_line_between_number_and_timestamp(self) -> None:
        text = "1\n\n00:00:00,000 --> 00:00:01,000\n空行\n"

        cues = parse_srt(self.write_srt(text))

        self.assertEqual([cue.duration_ms for cue in cues], [1000])

    def test_skips_cues_without_index_numbers(self) -> None:
        text = "00:00:00,000 --> 00:00:01,000\n无序号\n\n00:00:01,000 --> 00:00:02,000\n第二段\n"
        cues = parse_srt(self.write_srt(text))

        self.assertEqual([cue.duration_ms for cue in cues], [1000, 1000])

    def test_rejects_garbage_timestamp_line(self) -> None:
        text = "1\n00:00:00 --> 00:00:03\n少了毫秒\n"
        with self.assertRaises(SrtError) as ctx:
            parse_srt(self.write_srt(text))

        self.assertIn("不是合法的 SRT 时间戳", str(ctx.exception))

    def test_rejects_inverted_timestamps(self) -> None:
        text = "1\n00:00:05,000 --> 00:00:03,000\n倒序\n"
        with self.assertRaises(SrtError) as ctx:
            parse_srt(self.write_srt(text))

        self.assertIn("结束时间不晚于开始时间", str(ctx.exception))

    def test_rejects_empty_file(self) -> None:
        with self.assertRaises(SrtError) as ctx:
            parse_srt(self.write_srt("\n\n"))

        self.assertIn("没有可解析的段落", str(ctx.exception))

    def test_rejects_non_utf8_file_with_conversion_hint(self) -> None:
        path = self.tmp / "gbk.srt"
        path.write_bytes(BASIC_SRT.encode("gbk"))

        with self.assertRaises(SrtError) as ctx:
            parse_srt(path)

        self.assertIn("UTF-8", str(ctx.exception))
        self.assertIn("iconv", str(ctx.exception))

    def test_reports_missing_file(self) -> None:
        with self.assertRaises(SrtError) as ctx:
            parse_srt(self.tmp / "missing.srt")

        self.assertIn("找不到字幕文件", str(ctx.exception))

    def test_validate_timeline_flags_overlap(self) -> None:
        text = "1\n00:00:00,000 --> 00:00:02,000\nA\n\n2\n00:00:01,500 --> 00:00:03,000\nB\n"
        cues = parse_srt(self.write_srt(text))

        warnings = validate_timeline(cues)

        self.assertEqual(len(warnings), 1)
        self.assertIn("时间重叠 500ms", warnings[0])

    def test_validate_timeline_accepts_gaps(self) -> None:
        cues = parse_srt(self.write_srt(BASIC_SRT))
        self.assertEqual(validate_timeline(cues), [])

    def test_ms_to_srt_time_round_trip(self) -> None:
        self.assertEqual(ms_to_srt_time(3_450), "00:00:03,450")
        self.assertEqual(ms_to_srt_time(3_723_004), "01:02:03,004")


class ParseSrtCliTest(unittest.TestCase):
    def test_cli_prints_one_line_per_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "subtitles.srt"
            path.write_text(BASIC_SRT, encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main([str(path)])

        self.assertEqual(code, 0)
        self.assertIn("frame_01.png: 3.000s", stdout.getvalue())
        self.assertIn("[OK] 共 3 段，总时长 9.000s", stdout.getvalue())

    def test_cli_reports_bad_input_with_exit_code_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.srt"
            path.write_text("not an srt", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main([str(path)])

        self.assertEqual(code, 1)
        self.assertIn("[ERROR]", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
