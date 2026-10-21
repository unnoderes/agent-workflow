"""End-to-end tests: real FFmpeg, real MP4, real subtitle alignment.

Fixture generation uses FFmpeg's lavfi sources so the repository carries no
binary test assets: three solid-colour PNG frames, a 9 second MP3 and a
three-cue SRT, matching the acceptance scenario (3 frames + 9s audio).
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assemble_video import build_command, escape_filter_path, format_duration, main  # noqa: E402

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
REQUIRES_FFMPEG = unittest.skipUnless(
    FFMPEG and FFPROBE, "需要 FFmpeg 与 ffprobe 才能运行拼接测试"
)

FRAME_SIZE = "640x360"
# Frame 1 red, frame 2 green, frame 3 blue: the dominant channel tells us
# which frame FFmpeg is showing at a given timestamp.
FRAME_COLORS = ["0xFF0000", "0x00FF00", "0x0000FF"]
EXPECTED_CHANNEL = [0, 1, 2]
CUES = [(0, 3000), (3000, 6000), (6000, 9000)]
SRT = """1
00:00:00,000 --> 00:00:03,000
第一段

2
00:00:03,000 --> 00:00:06,000
第二段

3
00:00:06,000 --> 00:00:09,000
第三段
"""


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True)


def make_frame(path: Path, color: str, size: str = FRAME_SIZE) -> None:
    run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={size}:d=1",
            "-frames:v",
            "1",
            str(path),
        ]
    )


def make_audio(path: Path, seconds: float = 9.0) -> None:
    run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={seconds}",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(path),
        ]
    )


def sample_frame(video: Path, seconds: float, crop: str = "80:40:0:0") -> bytes:
    """Raw RGB bytes of one cropped frame at `seconds`."""
    return subprocess.run(
        [
            FFMPEG,
            "-v",
            "error",
            "-ss",
            f"{seconds}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            f"crop={crop}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        capture_output=True,
    ).stdout


def dominant_channel(video: Path, seconds: float) -> int:
    """Which colour channel is brightest in the top-left corner at `seconds`."""
    data = sample_frame(video, seconds)
    if not data:
        raise AssertionError(f"{video.name} 在 {seconds}s 没有画面")
    pixels = len(data) // 3
    totals = [sum(data[channel::3]) / pixels for channel in range(3)]
    return max(range(3), key=lambda channel: totals[channel])


def frame_channels(video: Path, size: str = "32x18") -> list[int]:
    """Dominant colour channel of every decoded frame, in display order."""
    width, height = (int(part) for part in size.split("x"))
    per_frame = width * height * 3
    data = subprocess.run(
        [
            FFMPEG,
            "-v",
            "error",
            "-i",
            str(video),
            "-vf",
            f"scale={size}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        capture_output=True,
    ).stdout

    channels: list[int] = []
    for start in range(0, len(data) - per_frame + 1, per_frame):
        frame = data[start : start + per_frame]
        totals = [sum(frame[channel::3]) for channel in range(3)]
        channels.append(max(range(3), key=lambda channel: totals[channel]))
    return channels


def count_white_pixels(video: Path, seconds: float) -> int:
    """Bright pixels in the lower third, where burned-in subtitles land."""
    data = sample_frame(video, seconds, crop="640:120:0:240")
    pixels = [tuple(data[i : i + 3]) for i in range(0, len(data), 3)]
    return sum(1 for pixel in pixels if min(pixel) > 200)


def probe(video: Path) -> dict:
    completed = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,codec_type,bit_rate,width,height",
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def create_project(root: Path) -> None:
    """Write the acceptance fixture: 3 frames, a 9 second MP3, 3 cues."""
    for name in ("画面", "音频", "字幕"):
        (root / name).mkdir(parents=True)
    for index, color in enumerate(FRAME_COLORS, start=1):
        make_frame(root / "画面" / f"frame_{index:02d}.png", color)
    make_audio(root / "音频" / "final.mp3")
    (root / "字幕" / "subtitles.srt").write_text(SRT, encoding="utf-8")


class ProjectAssembler(unittest.TestCase):
    """Base for tests that run the CLI in-process against `self.project`."""

    project: Path

    def assemble(self, *extra: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([str(self.project), *extra])
        return code, stdout.getvalue()


class BuildCommandTest(unittest.TestCase):
    """The exported stream configuration is part of the acceptance criteria."""

    def build(self, subtitles: str) -> list[str]:
        return build_command(
            "ffmpeg",
            manifest="concat_list.txt",
            audio="音频/final.mp3",
            srt="字幕/subtitles.srt",
            output="final_output.mp4",
            subtitles=subtitles,
            force_style="Fontsize=24",
            fps=30,
            preset="medium",
            crf=23,
            audio_bitrate="192k",
        )

    def test_encodes_h264_and_aac_192k_in_a_universal_pixel_format(self) -> None:
        command = self.build("none")

        self.assertEqual(command[command.index("-c:v") + 1], "libx264")
        self.assertEqual(command[command.index("-c:a") + 1], "aac")
        self.assertEqual(command[command.index("-b:a") + 1], "192k")
        self.assertEqual(command[command.index("-pix_fmt") + 1], "yuv420p")
        self.assertEqual(command[command.index("-preset") + 1], "medium")
        self.assertEqual(command[command.index("-crf") + 1], "23")
        self.assertIn("-shortest", command)

    def test_frame_rate_is_forced_by_a_filter_not_by_rate_conversion(self) -> None:
        command = self.build("none")

        self.assertNotIn("-r", command)
        self.assertEqual(command[command.index("-vf") + 1], "fps=30:round=down")

    def test_hard_subtitles_are_appended_to_the_filter_chain(self) -> None:
        command = self.build("hard")

        self.assertEqual(
            command[command.index("-vf") + 1],
            "fps=30:round=down,subtitles=字幕/subtitles.srt:force_style='Fontsize=24'",
        )
        self.assertNotIn("-c:s", command)

    def test_soft_subtitles_are_muxed_as_a_mov_text_track(self) -> None:
        command = self.build("soft")

        self.assertIn("字幕/subtitles.srt", command)
        self.assertEqual(command[command.index("-c:s") + 1], "mov_text")
        self.assertIn("language=chi", command)


class EscapeFilterPathTest(unittest.TestCase):
    def test_plain_relative_path_survives_unchanged(self) -> None:
        self.assertEqual(escape_filter_path("字幕/subtitles.srt"), "字幕/subtitles.srt")

    def test_windows_path_gets_colon_and_space_escaping(self) -> None:
        self.assertEqual(
            escape_filter_path(r"C:\my subs\字幕.srt"),
            "'C\\:/my subs/字幕.srt'",
        )

    def test_format_duration_uses_centiseconds(self) -> None:
        self.assertEqual(format_duration(9.0), "00:00:09.00")
        self.assertEqual(format_duration(3723.456), "01:02:03.46")


@REQUIRES_FFMPEG
class AssembleVideoEndToEndTest(ProjectAssembler):
    """Runs the real pipeline on a 3 frame / 9 second project."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # A space in the project path guards the FFmpeg filter escaping.
        self.project = Path(self._tmp.name) / "我的 项目"
        create_project(self.project)
        self.frames_dir = self.project / "画面"
        self.audio_dir = self.project / "音频"
        self.output = self.project / "final_output.mp4"

    def test_hard_subtitles_produce_a_playable_mp4(self) -> None:
        code, log = self.assemble()

        self.assertEqual(code, 0, log)
        self.assertTrue(self.output.is_file())
        self.assertTrue((self.project / "concat_list.txt").is_file())

        media = probe(self.output)
        streams = {stream["codec_type"]: stream for stream in media["streams"]}
        self.assertEqual(streams["video"]["codec_name"], "h264")
        self.assertEqual(streams["audio"]["codec_name"], "aac")
        self.assertEqual(
            (streams["video"]["width"], streams["video"]["height"]), (640, 360)
        )
        # ABR undershoots on a pure tone, so this only proves the audio track
        # is really encoded at roughly the requested rate.
        audio_kbps = int(streams["audio"]["bit_rate"]) / 1000
        self.assertGreater(audio_kbps, 120)
        self.assertAlmostEqual(float(media["format"]["duration"]), 9.0, delta=0.1)

    def test_frame_changes_land_on_the_cue_boundaries(self) -> None:
        code, log = self.assemble()
        self.assertEqual(code, 0, log)

        channels = frame_channels(self.output)
        self.assertEqual(len(channels), 270)  # 9 seconds at 30 fps

        transitions = [
            (index / 30, channels[index - 1], channels[index])
            for index in range(1, len(channels))
            if channels[index] != channels[index - 1]
        ]
        self.assertEqual(
            [(from_channel, to_channel) for _, from_channel, to_channel in transitions],
            [(0, 1), (1, 2)],
            "画面应该正好切换两次，按 SRT 顺序",
        )
        for (seconds, _, _), boundary in zip(transitions, (3.0, 6.0)):
            with self.subTest(boundary=boundary):
                self.assertLess(abs(seconds - boundary), 0.05)

    def test_hard_subtitles_are_burned_into_the_picture(self) -> None:
        code, log = self.assemble("--subtitles", "hard")
        self.assertEqual(code, 0, log)

        for start_ms, end_ms in CUES:
            middle = (start_ms + end_ms) / 2000
            with self.subTest(seconds=middle):
                self.assertGreater(count_white_pixels(self.output, middle), 0)

    def test_soft_subtitles_are_muxed_and_not_burned_in(self) -> None:
        code, log = self.assemble("--subtitles", "soft")

        self.assertEqual(code, 0, log)
        media = probe(self.output)
        subtitle_streams = [
            stream for stream in media["streams"] if stream["codec_type"] == "subtitle"
        ]
        self.assertEqual(len(subtitle_streams), 1)
        self.assertEqual(subtitle_streams[0]["codec_name"], "mov_text")
        self.assertEqual(count_white_pixels(self.output, 4.5), 0)

    def test_no_subtitles_leaves_no_subtitle_stream(self) -> None:
        code, log = self.assemble("--subtitles", "none")

        self.assertEqual(code, 0, log)
        media = probe(self.output)
        self.assertEqual(
            [stream for stream in media["streams"] if stream["codec_type"] == "subtitle"],
            [],
        )
        self.assertEqual(count_white_pixels(self.output, 4.5), 0)

    def test_audio_shorter_than_subtitles_is_padded_not_truncated(self) -> None:
        make_audio(self.audio_dir / "final.mp3", seconds=12.0)

        code, log = self.assemble("--subtitles", "none")

        self.assertEqual(code, 0, log)
        self.assertAlmostEqual(
            float(probe(self.output)["format"]["duration"]), 12.0, delta=0.1
        )
        self.assertIn("最后一帧已延长至音频结尾", log)
        # The closing frame keeps showing to the very end of the audio.
        self.assertEqual(dominant_channel(self.output, 11.9), EXPECTED_CHANNEL[2])


@REQUIRES_FFMPEG
class AssembleVideoErrorTest(ProjectAssembler):
    """Every rejection path prints one actionable message and exits 1."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name) / "project"
        create_project(self.project)
        self.frames_dir = self.project / "画面"
        self.audio = self.project / "音频" / "final.mp3"
        self.srt = self.project / "字幕" / "subtitles.srt"

    def test_missing_audio_points_at_tts_video(self) -> None:
        self.audio.unlink()

        code, log = self.assemble()

        self.assertEqual(code, 1)
        self.assertIn("缺少音频文件", log)
        self.assertIn("tts-video", log)

    def test_missing_subtitles_points_at_tts_video(self) -> None:
        self.srt.unlink()

        code, log = self.assemble()

        self.assertEqual(code, 1)
        self.assertIn("缺少字幕文件", log)
        self.assertIn("tts-video", log)

    def test_frame_and_cue_count_mismatch_is_fatal(self) -> None:
        make_frame(self.frames_dir / "frame_04.png", "0xFFFFFF")

        code, log = self.assemble()

        self.assertEqual(code, 1)
        self.assertIn("不一致", log)

    def test_non_utf8_subtitles_are_rejected(self) -> None:
        self.srt.write_bytes(SRT.encode("gbk"))

        code, log = self.assemble()

        self.assertEqual(code, 1)
        self.assertIn("UTF-8", log)

    def test_uneven_frame_size_is_rejected(self) -> None:
        for index, color in enumerate(FRAME_COLORS, start=1):
            make_frame(self.frames_dir / f"frame_{index:02d}.png", color, size="641x361")

        code, log = self.assemble()

        self.assertEqual(code, 1)
        self.assertIn("偶数", log)

    def test_mixed_frame_sizes_are_rejected(self) -> None:
        make_frame(self.frames_dir / "frame_02.png", "0x00FF00", size="800x450")

        code, log = self.assemble()

        self.assertEqual(code, 1)
        self.assertIn("尺寸不一致", log)

    def test_existing_output_needs_force(self) -> None:
        (self.project / "final_output.mp4").write_bytes(b"previous render")

        code, log = self.assemble()

        self.assertEqual(code, 1)
        self.assertIn("--force", log)

        code, log = self.assemble("--force", "--subtitles", "none")

        self.assertEqual(code, 0, log)
        self.assertGreater((self.project / "final_output.mp4").stat().st_size, 1000)

    def test_dry_run_writes_manifest_but_renders_nothing(self) -> None:
        code, log = self.assemble("--dry-run")

        self.assertEqual(code, 0, log)
        self.assertTrue((self.project / "concat_list.txt").is_file())
        self.assertFalse((self.project / "final_output.mp4").exists())
        self.assertIn("subtitles=", log)

    def test_failed_encode_reports_ffmpeg_stderr_and_leaves_no_output(self) -> None:
        code, log = self.assemble("--subtitles", "none", "--preset", "not-a-preset")

        self.assertEqual(code, 1)
        self.assertIn("FFmpeg 执行失败", log)
        self.assertFalse((self.project / "final_output.mp4").exists())

    def test_missing_project_dir_is_reported(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([str(Path(self._tmp.name) / "nope")])

        self.assertEqual(code, 1)
        self.assertIn("项目目录不存在", stdout.getvalue())

    def test_custom_output_name(self) -> None:
        code, log = self.assemble("--output", "demo.mp4", "--subtitles", "none")

        self.assertEqual(code, 0, log)
        self.assertTrue((self.project / "demo.mp4").is_file())


if __name__ == "__main__":
    unittest.main()
