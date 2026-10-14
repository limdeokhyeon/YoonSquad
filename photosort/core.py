"""JPG/RAW 분류 핵심 로직 (GUI와 무관, 표준 라이브러리만 사용)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

JPG_EXTS = {".jpg", ".jpeg"}
# 소니(.arw, .sr2, .srf)를 맨 앞에 두고 다른 브랜드도 함께 지원
RAW_EXTS = {
    ".arw", ".sr2", ".srf",  # Sony
    ".cr2", ".cr3", ".crw",  # Canon
    ".nef", ".nrw",  # Nikon
    ".raf",  # Fujifilm
    ".orf",  # Olympus / OM System
    ".rw2",  # Panasonic
    ".pef",  # Pentax
    ".dng",  # Adobe / Leica 등
    ".srw", ".3fr", ".erf", ".kdc", ".mrw", ".x3f", ".iiq", ".raw",
}
JPG_DIR = "JPG"
RAW_DIR = "RAW"


@dataclass
class Options:
    move: bool = False  # False: 복사(안전), True: 이동
    by_date: bool = False  # 날짜별 폴더(YYYY-MM-DD) 아래에 JPG/RAW 생성
    recursive: bool = False  # 하위 폴더 포함 (SD카드 DCIM 등)
    dest: Path | None = None  # 결과를 둘 폴더. None이면 선택한 폴더 안에 생성


@dataclass
class Item:
    src: Path
    kind: str  # "jpg" | "raw"
    dst: Path


@dataclass
class Plan:
    items: list[Item] = field(default_factory=list)
    pairs: int = 0
    jpg_only: list[Path] = field(default_factory=list)
    raw_only: list[Path] = field(default_factory=list)

    @property
    def jpg_count(self) -> int:
        return sum(1 for i in self.items if i.kind == "jpg")

    @property
    def raw_count(self) -> int:
        return sum(1 for i in self.items if i.kind == "raw")


@dataclass
class Result:
    done: int = 0
    errors: list[str] = field(default_factory=list)


def classify(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in JPG_EXTS:
        return "jpg"
    if ext in RAW_EXTS:
        return "raw"
    return None


def _iter_files(folder: Path, recursive: bool) -> Iterable[Path]:
    for p in sorted(folder.iterdir()):
        # 맥 SD카드의 '._DSC0001.ARW' 같은 숨김/리소스포크 파일은 제외
        if p.name.startswith("."):
            continue
        if p.is_dir():
            if recursive and p.name not in (JPG_DIR, RAW_DIR):
                yield from _iter_files(p, recursive)
        elif p.is_file():
            yield p


def _unique(dst: Path, taken: set[Path]) -> Path:
    """이미 있거나 이번 계획에서 쓰는 이름이면 _1, _2 ... 를 붙인다."""
    cand, n = dst, 1
    while cand.exists() or cand in taken:
        cand = dst.with_name(f"{dst.stem}_{n}{dst.suffix}")
        n += 1
    return cand


def _same_file(a: Path, b: Path) -> bool:
    try:
        sa, sb = a.stat(), b.stat()
    except OSError:
        return False
    return sa.st_size == sb.st_size and int(sa.st_mtime) == int(sb.st_mtime)


def build_plan(folder: Path, opts: Options) -> Plan:
    folder = Path(folder)
    root = Path(opts.dest) if opts.dest else folder
    plan = Plan()
    taken: set[Path] = set()
    stems: dict[tuple[Path, str], set[str]] = {}

    for src in _iter_files(folder, opts.recursive):
        kind = classify(src)
        if kind is None:
            continue
        base = root
        if opts.by_date:
            base = base / datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d")
        dst = base / (JPG_DIR if kind == "jpg" else RAW_DIR) / src.name
        if dst.exists() and _same_file(src, dst):
            # 이전 실행에서 이미 정리된 파일: 계획에 넣지 않는다
            continue
        dst = _unique(dst, taken)
        taken.add(dst)
        plan.items.append(Item(src, kind, dst))
        stems.setdefault((src.parent, src.stem.lower()), set()).add(kind)

    kinds_by_stem = stems
    for item in plan.items:
        kinds = kinds_by_stem[(item.src.parent, item.src.stem.lower())]
        if kinds == {"jpg", "raw"}:
            continue
        (plan.jpg_only if item.kind == "jpg" else plan.raw_only).append(item.src)
    plan.pairs = sum(1 for k in kinds_by_stem.values() if k == {"jpg", "raw"})
    return plan


def execute(
    plan: Plan,
    opts: Options,
    progress: Callable[[int, int, Item], None] | None = None,
) -> Result:
    res = Result()
    total = len(plan.items)
    for i, item in enumerate(plan.items, 1):
        try:
            item.dst.parent.mkdir(parents=True, exist_ok=True)
            if opts.move:
                shutil.move(str(item.src), str(item.dst))
            else:
                shutil.copy2(item.src, item.dst)
            res.done += 1
        except OSError as e:
            res.errors.append(f"{item.src.name}: {e}")
        if progress:
            progress(i, total, item)
    return res
