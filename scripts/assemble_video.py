"""Assemble PNG frames + MP3 audio + SRT subtitles into a final MP4.

This is the `assemble-video` skill's engine: it validates the inputs, derives
one frame duration per subtitle cue, writes an FFmpeg concat manifest and runs
one FFmpeg pass that produces a H.264 / AAC 192 kbps MP4, with the subtitles
burned in, muxed as a soft track, or left out.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from generate_concat_list import ConcatError, build_plan, list_frame_files
from parse_srt_durations import SrtError

PROJECT_DIRS = {
    "frames": "画面",
    "audio": "音频/final.mp3",
    "srt": "字幕/subtitles.srt",
}
DEFAULT_OUTPUT = "final_output.mp4"
DEFAULT_MANIFEST = "concat_list.txt"
DEFAULT_FORCE_STYLE = (
    "Fontsize={font_size},PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2"
)
FFMPEG_INSTALL_HINT = (
    "  Windows: winget install FFmpeg.FFmpeg\n"
    "  macOS:   brew install ffmpeg\n"
    "  Linux:   sudo apt install ffmpeg"
)


class AssembleError(RuntimeError):
    """Raised for anything the user can fix before FFmpeg runs."""


def info(message: str) -> None:
    print(f"[INFO] {message}", flush=True)


def ok(message: str) -> None:
    print(f"[OK] {message}", flush=True)


def warn(message: str) -> None:
    print(f"[WARN] {message}", flush=True)


def error(message: str) -> None:
    print(f"[ERROR] {message}", flush=True)


def force_utf8_when_redirected() -> None:
    """Write UTF-8 when stdout/stderr are redirected.

    On Windows a redirected stream falls back to the locale code page (cp936,
    cp1252, …), which turns the Chinese progress messages into mojibake in
    pipes and log files. A real console already handles Unicode itself, so it
    is left alone.
    """
    for stream in (sys.stdout, sys.stderr):
        if stream is None or stream.isatty() or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # stream already detached
            pass


def format_duration(seconds: float) -> str:
    """Format seconds as `HH:MM:SS.mm`."""
    centis = round(seconds * 100)
    minutes, centis = divmod(centis, 6000)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{centis // 100:02d}.{centis % 100:02d}"


def escape_filter_path(path: str | Path) -> str:
    """Escape a path for an FFmpeg filter option value (`subtitles=`).

    Filter options are parsed twice, so `:`, `,`, `;`, `[`, `]` and `'` need
    escaping; spaces are handled by wrapping the value in quotes. Backslashes
    are normalised to `/`, which FFmpeg accepts on every platform.
    """
    text = str(path).replace("\\", "/")
    for char in ("'", ":", ",", ";", "[", "]"):
        text = text.replace(char, "\\" + char)
    if " " in text:
        text = f"'{text}'"
    return text


def check_ffmpeg() -> tuple[str, str]:
    """Return the ffmpeg and ffprobe executables, or fail with install hints."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not (ffmpeg and ffprobe):
        missing = [
            name
            for name, path in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe))
            if not path
        ]
        raise AssembleError(
            f"未找到 {'、'.join(missing)}，请先安装 FFmpeg：\n{FFMPEG_INSTALL_HINT}"
        )
    return ffmpeg, ffprobe


def read_png_header(path: str | Path) -> tuple[int, int, int]:
    """Return `(width, height, color_type)` from a PNG IHDR chunk."""
    path = Path(path)
    with path.open("rb") as handle:
        header = handle.read(26)
    if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise AssembleError(f"不是有效的 PNG 文件（缺少 IHDR）：{path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height, header[25]


def validate_frames(frames: list[Path]) -> tuple[int, int, list[str]]:
    """Check that every frame can be concatenated into one H.264 stream."""
    sizes: dict[tuple[int, int], list[Path]] = {}
    transparent: list[Path] = []
    for frame in frames:
        width, height, color_type = read_png_header(frame)
        sizes.setdefault((width, height), []).append(frame)
        if color_type in (4, 6):
            transparent.append(frame)

    if len(sizes) > 1:
        detail = "\n".join(
            f"  {width}x{height}: {len(paths)} 帧（例如 {paths[0].name}）"
            for (width, height), paths in sorted(sizes.items())
        )
        raise AssembleError(f"画面帧尺寸不一致，无法拼接：\n{detail}")

    (width, height), _ = next(iter(sizes.items()))
    if width % 2 or height % 2:
        raise AssembleError(
            f"画面尺寸 {width}x{height} 含奇数像素，H.264 的 yuv420p 要求宽高都是偶数"
        )

    warnings = []
    if transparent:
        warnings.append(
            f"{len(transparent)} 帧 PNG 带透明通道（例如 {transparent[0].name}），"
            "透明区域会被合成为黑色"
        )
    return width, height, warnings


def probe_media(ffprobe: str, path: str | Path) -> dict:
    """Return duration plus the stream list of a media file via ffprobe."""
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_name,codec_type,width,height,bit_rate,duration",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise AssembleError(f"ffprobe 无法读取 {path}：\n{completed.stderr.strip()}")

    payload = json.loads(completed.stdout or "{}")
    duration = 0.0
    try:
        duration = float(payload.get("format", {}).get("duration", 0.0))
    except (TypeError, ValueError):
        duration = 0.0
    return {"duration": duration, "streams": payload.get("streams", [])}


def probe_duration(ffprobe: str, path: str | Path) -> float:
    return probe_media(ffprobe, path)["duration"]


def resolve_input(project_dir: Path, value: str) -> Path:
    """Resolve a user-supplied path against the project directory."""
    path = Path(value)
    return path if path.is_absolute() else project_dir / path


def relative_to_project(project_dir: Path, path: Path) -> str:
    """Shortest FFmpeg argument for `path`, given FFmpeg runs in the project."""
    try:
        return os.path.relpath(path, project_dir).replace("\\", "/")
    except ValueError:  # different Windows drives
        return str(path)


def build_command(
    ffmpeg: str,
    *,
    manifest: str,
    audio: str,
    srt: str,
    output: str,
    subtitles: str,
    force_style: str,
    fps: int,
    preset: str,
    crf: int,
    audio_bitrate: str,
) -> list[str]:
    """Build the single FFmpeg pass that renders the final MP4."""
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        manifest,
        "-i",
        audio,
    ]
    if subtitles == "soft":
        command += ["-i", srt]

    # `round=down` keeps every cue exactly on its boundary: the picture changes
    # when the instant arrives instead of up to half an input tick before it.
    # `-r` cannot be used here, its implicit rate conversion rounds earlier.
    filters = [f"fps={fps}:round=down"]
    if subtitles == "hard":
        filters.append(
            f"subtitles={escape_filter_path(srt)}:force_style='{force_style}'"
        )
    command += ["-vf", ",".join(filters)]

    command += [
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        audio_bitrate,
    ]
    if subtitles == "soft":
        command += ["-c:s", "mov_text", "-metadata:s:s:0", "language=chi"]

    command += ["-shortest", "-progress", "pipe:1", "-nostats", output]
    return command


def run_ffmpeg(command: list[str], project_dir: Path, expected_sec: float) -> None:
    """Run FFmpeg in `project_dir`, reporting progress and failing loudly.

    FFmpeg's stderr goes to a temporary file rather than a pipe: it can be
    verbose on failure, and reading two pipes from one process risks deadlock.
    """
    with tempfile.TemporaryFile(
        mode="w+", encoding="utf-8", errors="replace"
    ) as error_stream:
        with subprocess.Popen(
            command,
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=error_stream,
            text=True,
            encoding="utf-8",
            errors="replace",
        ) as process:
            reported = 0
            assert process.stdout is not None
            for line in process.stdout:
                if not line.startswith("out_time_us=") or expected_sec <= 0:
                    continue
                try:
                    done_sec = int(line.split("=", 1)[1].strip()) / 1_000_000
                except ValueError:
                    continue
                percent = min(99, int(done_sec / expected_sec * 100))
                if percent >= reported + 10:
                    reported = percent - percent % 10
                    info(f"编码进度：{reported}% ({done_sec:.1f}s / {expected_sec:.1f}s)")

            returncode = process.wait()

        error_stream.seek(0)
        stderr = error_stream.read().strip()

    if returncode != 0:
        raise AssembleError(f"FFmpeg 执行失败（退出码 {returncode}）：\n{stderr}")
    for line in stderr.splitlines():
        warn(f"FFmpeg: {line}")


def summarize(
    *, output: Path, media: dict, audio_sec: float, subtitles: str, size_mb: float
) -> None:
    label = {"hard": "硬字幕烧录", "soft": "软字幕封装", "none": "无字幕"}[subtitles]
    video = next((s for s in media["streams"] if s.get("codec_type") == "video"), {})
    audio = next((s for s in media["streams"] if s.get("codec_type") == "audio"), {})
    resolution = f"{video.get('width', '?')}x{video.get('height', '?')}"

    print()
    print("[SUCCESS] 视频生成完成！")
    print(f"- 路径：{output}")
    print(f"- 大小：{size_mb:.1f} MB")
    print(f"- 时长：{format_duration(media['duration'])}")
    print(f"- 分辨率：{resolution}")
    print(f"- 编码：{video.get('codec_name', '?').upper()} + {audio.get('codec_name', '?').upper()}")
    print(f"- 字幕：{label}")

    drift = media["duration"] - audio_sec
    if abs(drift) > 0.1:
        warn(f"输出时长与音频相差 {drift:+.3f}s，请检查字幕时间轴")
    print()
    print("[INFO] 预览命令：")
    print(f"  ffplay \"{output}\"")


def assemble(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        raise AssembleError(f"项目目录不存在：{project_dir}")

    info("检查依赖…")
    ffmpeg, ffprobe = check_ffmpeg()
    ok(f"FFmpeg 已安装：{ffmpeg}")

    frames_dir = resolve_input(project_dir, args.frames_dir)
    audio = resolve_input(project_dir, args.audio)
    srt = resolve_input(project_dir, args.srt)
    output = resolve_input(project_dir, args.output)

    if not audio.is_file():
        raise AssembleError(
            f"缺少音频文件：{audio}\n  请先运行 tts-video 生成 音频/final.mp3。"
        )
    if not srt.is_file():
        raise AssembleError(
            f"缺少字幕文件：{srt}\n  请先运行 tts-video 生成 字幕/subtitles.srt。"
        )
    if output.exists() and not args.force:
        raise AssembleError(
            f"输出文件已存在：{output}\n"
            "  确认可以覆盖后重新运行并加上 --force，或改用 --output 指定新文件名。"
        )

    try:
        frames = list_frame_files(frames_dir)
    except ConcatError as exc:
        raise AssembleError(str(exc)) from exc
    ok(f"找到 {len(frames)} 个 PNG 帧")

    width, height, frame_warnings = validate_frames(frames)
    ok(f"画面尺寸 {width}x{height}，全部帧一致")
    for message in frame_warnings:
        warn(message)

    audio_sec = probe_duration(ffprobe, audio)
    ok(f"音频文件存在（{audio_sec:.2f}s）")

    try:
        plan = build_plan(srt, frames_dir, project_dir / args.manifest, pad_to_sec=audio_sec)
    except (ConcatError, SrtError) as exc:
        raise AssembleError(str(exc)) from exc
    plan.write()
    ok(f"字幕文件存在（{plan.frame_count} 段）")
    ok(f"concat 清单：{plan.output_path.name}，总时长 {plan.total_duration_ms / 1000:.3f}s")
    for message in plan.warnings:
        warn(message)

    force_style = args.force_style or DEFAULT_FORCE_STYLE.format(font_size=args.font_size)
    command = build_command(
        ffmpeg,
        manifest=relative_to_project(project_dir, plan.output_path),
        audio=relative_to_project(project_dir, audio),
        srt=relative_to_project(project_dir, srt),
        output=relative_to_project(project_dir, output),
        subtitles=args.subtitles,
        force_style=force_style,
        fps=args.fps,
        preset=args.preset,
        crf=args.crf,
        audio_bitrate=args.audio_bitrate,
    )

    if args.dry_run:
        info("dry-run，未执行 FFmpeg：")
        print("  " + " ".join(f'"{part}"' if " " in part else part for part in command))
        return 0

    info("执行 FFmpeg 拼接…")
    try:
        run_ffmpeg(command, project_dir, plan.total_duration_ms / 1000)
    except AssembleError:
        # A half-written MP4 is unusable and would block the next run behind
        # the overwrite guard, so never leave one behind.
        output.unlink(missing_ok=True)
        raise

    if not output.is_file():
        raise AssembleError(f"FFmpeg 未生成输出文件：{output}")
    media = probe_media(ffprobe, output)
    summarize(
        output=output,
        media=media,
        audio_sec=audio_sec,
        subtitles=args.subtitles,
        size_mb=output.stat().st_size / (1024 * 1024),
    )
    return 0


def valid_choice(value: str) -> str:
    if value not in ("hard", "soft", "none"):
        raise argparse.ArgumentTypeError(
            f"字幕模式只支持 hard/soft/none，收到：{value}"
        )
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 PNG 帧序列 + MP3 音频 + SRT 字幕拼接为最终 MP4（FFmpeg）"
    )
    parser.add_argument("project_dir", help="视频项目目录（包含 画面/ 音频/ 字幕/）")
    parser.add_argument(
        "--subtitles",
        type=valid_choice,
        default="hard",
        help="字幕模式：hard 烧录（默认）/ soft 封装 / none 无字幕",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"输出文件名（默认 {DEFAULT_OUTPUT}）")
    parser.add_argument("--frames-dir", default=PROJECT_DIRS["frames"], help=f"PNG 帧目录（默认 {PROJECT_DIRS['frames']}）")
    parser.add_argument("--audio", default=PROJECT_DIRS["audio"], help=f"音频文件（默认 {PROJECT_DIRS['audio']}）")
    parser.add_argument("--srt", default=PROJECT_DIRS["srt"], help=f"字幕文件（默认 {PROJECT_DIRS['srt']}）")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help=f"concat 清单路径（默认 {DEFAULT_MANIFEST}）")
    parser.add_argument("--fps", type=int, default=30, help="输出帧率（默认 30；决定字幕对齐精度，1/30s≈33ms）")
    parser.add_argument("--preset", default="medium", help="libx264 preset（默认 medium）")
    parser.add_argument("--crf", type=int, default=23, help="libx264 CRF，越小越好（默认 23）")
    parser.add_argument("--audio-bitrate", default="192k", help="AAC 码率（默认 192k）")
    parser.add_argument("--font-size", type=int, default=24, help="硬字幕字号（默认 24）")
    parser.add_argument("--force-style", default=None, help="覆盖完整的 ASS 样式串（高级用法）")
    parser.add_argument("--force", action="store_true", help="允许覆盖已存在的输出文件")
    parser.add_argument("--dry-run", action="store_true", help="只检查输入并打印 FFmpeg 命令，不执行")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    force_utf8_when_redirected()
    args = parse_args(argv)
    try:
        return assemble(args)
    except AssembleError as exc:
        error(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
