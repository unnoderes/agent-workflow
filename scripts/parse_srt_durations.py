"""Parse SRT subtitle files into per-cue timings.

`assemble-video` shows one PNG frame per SRT cue, so cue durations decide how
long each frame stays on screen. Everything below works in integer
milliseconds to keep frame boundaries exact.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# `00:00:03,450 --> 00:00:06,900`; `.` is accepted as the decimal separator
# because some tools write it that way.
_TIMESTAMP = re.compile(
    r"(\d{1,3}):([0-5]\d):([0-5]\d)[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,3}):([0-5]\d):([0-5]\d)[,.](\d{1,3})"
)


class SrtError(ValueError):
    """Raised when an SRT file cannot be turned into a reliable timeline."""


@dataclass(frozen=True)
class SrtCue:
    """One subtitle cue, with absolute times in milliseconds."""

    index: int
    start_ms: int
    end_ms: int
    text: str = ""

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    @property
    def duration_sec(self) -> float:
        return self.duration_ms / 1000.0


def _fraction_to_ms(fraction: str) -> int:
    """`5` -> 500ms, `45` -> 450ms, `450` -> 450ms."""
    return int((fraction + "00")[:3])


def _to_ms(hours: str, minutes: str, seconds: str, fraction: str) -> int:
    total = (int(hours) * 60 + int(minutes)) * 60 + int(seconds)
    return total * 1000 + _fraction_to_ms(fraction)


def ms_to_srt_time(ms: int) -> str:
    """Format milliseconds as `HH:MM:SS,mmm`."""
    hours, ms = divmod(int(ms), 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    seconds, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def read_srt_text(path: str | Path) -> str:
    """Read an SRT file as text, rejecting anything that is not UTF-8."""
    path = Path(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise SrtError(f"找不到字幕文件：{path}") from None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SrtError(
            f"字幕文件不是 UTF-8 编码：{path}\n"
            f"  请先转换编码，例如：iconv -f GBK -t UTF-8 \"{path}\" > subtitles.utf8.srt"
        ) from exc


def parse_srt(path: str | Path) -> list[SrtCue]:
    """Parse an SRT file into cues, in file order.

    Raises `SrtError` with the offending line when the file is malformed, so
    the message can be shown to the user as-is.
    """
    path = Path(path)
    text = read_srt_text(path)
    lines = text.splitlines()
    cues: list[SrtCue] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        index_line = i + 1
        if line.isdigit():  # cue number, optional for our purposes
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1  # tolerate a blank line between number and timestamp
            if i >= len(lines):
                raise SrtError(f"{path} 第 {index_line} 行只有序号，缺少时间戳")
            line = lines[i].strip()

        match = _TIMESTAMP.match(line)
        if match is None:
            raise SrtError(
                f"{path} 第 {i + 1} 行不是合法的 SRT 时间戳：{line!r}\n"
                "  期望格式：00:00:03,450 --> 00:00:06,900"
            )

        start_ms = _to_ms(*match.group(1, 2, 3, 4))
        end_ms = _to_ms(*match.group(5, 6, 7, 8))
        if end_ms <= start_ms:
            raise SrtError(f"{path} 第 {i + 1} 行结束时间不晚于开始时间：{line!r}")

        i += 1
        body: list[str] = []
        while i < len(lines) and lines[i].strip():
            body.append(lines[i].strip())
            i += 1

        cues.append(
            SrtCue(
                index=len(cues) + 1,
                start_ms=start_ms,
                end_ms=end_ms,
                text=" ".join(body),
            )
        )

    if not cues:
        raise SrtError(f"字幕文件里没有可解析的段落：{path}")
    return cues


def parse_srt_durations(srt_path: str | Path) -> list[float]:
    """Per-cue durations in seconds, in file order."""
    return [cue.duration_sec for cue in parse_srt(srt_path)]


def validate_timeline(cues: list[SrtCue]) -> list[str]:
    """Return warnings for cues that overlap, which breaks one-frame-per-cue."""
    warnings: list[str] = []
    for previous, current in zip(cues, cues[1:]):
        if current.start_ms < previous.end_ms:
            warnings.append(
                f"第 {previous.index} 段与第 {current.index} 段时间重叠 "
                f"{previous.end_ms - current.start_ms}ms"
            )
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="解析 SRT 时间戳，输出每段时长（供 assemble-video 使用）"
    )
    parser.add_argument("srt_file", help="SRT 字幕文件路径")
    args = parser.parse_args(argv)

    try:
        cues = parse_srt(args.srt_file)
    except SrtError as exc:
        print(f"[ERROR] {exc}")
        return 1

    total_ms = 0
    for cue in cues:
        print(f"frame_{cue.index:02d}.png: {cue.duration_sec:.3f}s")
        total_ms += cue.duration_ms
    print(f"[OK] 共 {len(cues)} 段，总时长 {total_ms / 1000:.3f}s")

    for warning in validate_timeline(cues):
        print(f"[WARN] {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
