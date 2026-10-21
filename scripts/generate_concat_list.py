"""Turn SRT cue durations into an FFmpeg concat demuxer manifest.

One PNG frame per SRT cue: the cue duration becomes the frame's display
duration. The manifest is read by the concat demuxer with `-safe 0`, so paths
may be anywhere; they are written relative to the manifest so the whole
project directory stays movable.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from parse_srt_durations import SrtError, validate_timeline
from parse_srt_durations import parse_srt

_FRAME_NAME = re.compile(r"^frame_(\d+)\.png$", re.IGNORECASE)


class ConcatError(ValueError):
    """Raised when frames and subtitles cannot be paired into a timeline."""


@dataclass(frozen=True)
class ConcatEntry:
    """One frame and how long it stays on screen."""

    frame: Path
    duration_ms: int


@dataclass
class ConcatPlan:
    """The full frame timeline plus the manifest path it is written to."""

    entries: list[ConcatEntry]
    output_path: Path
    warnings: list[str] = field(default_factory=list)

    @property
    def total_duration_ms(self) -> int:
        return sum(entry.duration_ms for entry in self.entries)

    @property
    def frame_count(self) -> int:
        return len(self.entries)

    def render(self) -> str:
        """Render the concat demuxer manifest.

        The final frame is listed again without a duration: the demuxer
        ignores the duration of the last entry, so the repeat is what makes
        the closing frame last until the end of the audio.
        """
        lines: list[str] = []
        for entry in self.entries:
            lines.append(f"file '{_manifest_path(entry.frame, self.output_path)}'")
            lines.append(f"duration {entry.duration_ms / 1000:.3f}")
        lines.append(f"file '{_manifest_path(self.entries[-1].frame, self.output_path)}'")
        return "\n".join(lines) + "\n"

    def write(self) -> Path:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" keeps the manifest byte-identical on Windows and POSIX.
        self.output_path.write_text(self.render(), encoding="utf-8", newline="\n")
        return self.output_path


def _manifest_path(frame: Path, manifest: Path) -> str:
    """Path of `frame` as written into a manifest sitting at `manifest`."""
    frame = Path(frame).resolve()
    try:
        relative = os.path.relpath(frame, Path(manifest).resolve().parent)
    except ValueError:  # different Windows drives -> no relative path exists
        relative = str(frame)
    # FFmpeg accepts forward slashes on every platform; a literal `'` inside a
    # quoted concat path is escaped as `'\''`.
    return relative.replace("\\", "/").replace("'", "'\\''")


def list_frame_files(frames_dir: str | Path) -> list[Path]:
    """Return `frame_N.png` files in `frames_dir`, ordered by N."""
    frames_dir = Path(frames_dir)
    if not frames_dir.is_dir():
        raise ConcatError(f"找不到画面目录：{frames_dir}")

    numbered: list[tuple[int, Path]] = []
    for path in frames_dir.iterdir():
        match = _FRAME_NAME.match(path.name)
        if match and path.is_file():
            numbered.append((int(match.group(1)), path))

    if not numbered:
        raise ConcatError(
            f"画面目录里没有 frame_*.png：{frames_dir}\n"
            "  请先导出画面帧（html-image-export）。"
        )
    numbered.sort(key=lambda item: item[0])
    return [path for _, path in numbered]


def build_plan(
    srt_path: str | Path,
    frames_dir: str | Path,
    output_path: str | Path,
    pad_to_sec: float | None = None,
) -> ConcatPlan:
    """Pair every frame with a cue duration and prepare the manifest.

    `pad_to_sec` is the audio duration: when the subtitles end earlier, the
    closing frame is extended so the video covers the whole audio track, and
    when they end later a warning is recorded because the tail gets cut.
    """
    try:
        cues = parse_srt(srt_path)
    except SrtError as exc:
        raise ConcatError(str(exc)) from exc

    frames = list_frame_files(frames_dir)
    if len(frames) != len(cues):
        raise ConcatError(
            f"画面帧数与字幕段数不一致：{len(frames)} 个 PNG 帧 vs {len(cues)} 段字幕\n"
            f"  画面目录：{frames_dir}\n"
            f"  字幕文件：{srt_path}\n"
            "  请确认 html-image-export 导出了全部帧，且字幕与帧一一对应。"
        )

    entries = [
        ConcatEntry(frame=frame, duration_ms=cue.duration_ms)
        for frame, cue in zip(frames, cues)
    ]
    warnings = validate_timeline(cues)

    if pad_to_sec is not None:
        target_ms = round(pad_to_sec * 1000)
        delta_ms = target_ms - sum(entry.duration_ms for entry in entries)
        if delta_ms > 0:
            last = entries[-1]
            entries[-1] = ConcatEntry(
                frame=last.frame, duration_ms=last.duration_ms + delta_ms
            )
            warnings.append(
                f"字幕总时长比音频短 {delta_ms / 1000:.3f}s，最后一帧已延长至音频结尾"
            )
        elif delta_ms < -100:
            warnings.append(
                f"字幕总时长比音频长 {-delta_ms / 1000:.3f}s，"
                "输出会被裁剪到音频长度，末尾画面可能不完整"
            )

    return ConcatPlan(
        entries=entries, output_path=Path(output_path), warnings=warnings
    )


def generate_concat_list(
    srt_path: str | Path,
    frames_dir: str | Path,
    output_path: str | Path,
    pad_to_sec: float | None = None,
) -> ConcatPlan:
    """Build the plan and write the manifest to disk."""
    plan = build_plan(srt_path, frames_dir, output_path, pad_to_sec=pad_to_sec)
    plan.write()
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="根据 SRT 时间戳生成 FFmpeg concat 清单"
    )
    parser.add_argument("srt_file", help="SRT 字幕文件路径")
    parser.add_argument("frames_dir", help="PNG 帧目录（frame_01.png …）")
    parser.add_argument("output_file", help="输出的 concat 清单路径")
    parser.add_argument(
        "--pad-to",
        type=float,
        default=None,
        metavar="SECONDS",
        help="音频时长（秒）：字幕偏短时延长最后一帧",
    )
    args = parser.parse_args(argv)

    try:
        plan = generate_concat_list(
            args.srt_file, args.frames_dir, args.output_file, pad_to_sec=args.pad_to
        )
    except ConcatError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] 已生成 concat 清单：{plan.output_path}")
    print(f"[OK] 帧数：{plan.frame_count}，总时长：{plan.total_duration_ms / 1000:.3f}s")
    for warning in plan.warnings:
        print(f"[WARN] {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
