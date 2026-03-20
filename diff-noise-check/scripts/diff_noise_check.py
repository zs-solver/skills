#!/usr/bin/env python3
"""判断改动是否仅为空白、横线、Markdown 表格列对齐。"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_HR = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
_YAML_KEY = re.compile(r"^[\w.-]+\s*:\s")
_SEP_CELL = re.compile(r"^[\-:\s]+$")


def _fm_span(lines: list[str]) -> tuple[int, int] | None:
    if not lines or not _HR.match(lines[0].rstrip("\n\r")):
        return None
    j = 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j >= len(lines) or not _YAML_KEY.match(lines[j].rstrip("\n\r")):
        return None
    for k in range(1, len(lines)):
        if _HR.match(lines[k].rstrip("\n\r")):
            return (0, k)
    return None


def _table_row_norm(s: str) -> str:
    if not re.match(r"^\s*\|", s):
        return s
    cells = [c.strip() for c in s.strip().split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop(-1)
    norm = ["---" if (c and _SEP_CELL.match(c)) else c for c in cells]
    return "| " + " | ".join(norm) + " |"


def normalize(text: str) -> str:
    lines = text.splitlines()
    fm = _fm_span(lines)
    acc: list[str] = []
    for i, raw in enumerate(lines):
        s = raw.rstrip("\n\r").rstrip()
        if fm and fm[0] <= i <= fm[1]:
            acc.append(s)
            continue
        if not s.strip() or _HR.match(s):
            continue
        acc.append(_table_row_norm(s))
    return "\n".join(acc)


def git(repo: Path, *a: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def show(repo: Path, spec: str) -> str | None:
    p = git(repo, "show", spec)
    return p.stdout if p.returncode == 0 else None


def _report(rel: str, ok: bool, raw_old: str, raw_new: str) -> None:
    if ok:
        st, det = (
            ("仅噪声", "与基准完全一致（含空白与格式）")
            if raw_old == raw_new
            else ("仅噪声", "剥离空白、横线与表格对齐后一致，无实质修改")
        )
    else:
        st, det = ("有实质差异", "剥离噪声后仍有差异（存在实质修改）")
    print(rel)
    print(f"  {st}\t{det}")


def find_repo(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("no .git", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--unstaged", action="store_true")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()

    if args.compare:
        if args.paths or args.staged or args.unstaged or args.base != "HEAD" or args.repo:
            print("--compare conflicts with other git options", file=sys.stderr)
            return 2
        pa, pb = (Path(x).expanduser().resolve() for x in args.compare)
        o, n = (
            pa.read_text(encoding="utf-8", errors="replace"),
            pb.read_text(encoding="utf-8", errors="replace"),
        )
        ok = normalize(o) == normalize(n)
        _report(f"{pa.name} -> {pb.name}", ok, o, n)
        return 0 if ok else 1

    repo = args.repo.resolve() if args.repo else find_repo(Path.cwd())
    brp = git(repo, "rev-parse", "--verify", args.base)
    if brp.returncode:
        print(brp.stderr.strip() or "rev-parse failed", file=sys.stderr)
        return 2
    br = brp.stdout.strip()

    if args.paths:
        paths = [p.replace("\\", "/").strip("/") for p in args.paths]
    elif args.unstaged:
        paths = [x for x in git(repo, "diff", "--name-only", "-z").stdout.split("\0") if x]
    elif args.staged:
        paths = [x for x in git(repo, "diff", "--cached", "--name-only", "-z", br).stdout.split("\0") if x]
    else:
        paths = [x for x in git(repo, "diff", "--name-only", "-z", br).stdout.split("\0") if x]

    if not paths:
        print("（无）\t—\t相对基准无改动文件")
        return 0

    bad = False
    for i, rel in enumerate(paths):
        if args.unstaged:
            o = show(repo, f":0:{rel}") or show(repo, f"{br}:{rel}")
            fp = repo / rel
            n = fp.read_text(encoding="utf-8", errors="replace") if fp.is_file() else ""
        elif args.staged:
            o, n = show(repo, f"{br}:{rel}") or "", show(repo, f":0:{rel}") or ""
        else:
            o = show(repo, f"{br}:{rel}") or ""
            fp = repo / rel
            n = fp.read_text(encoding="utf-8", errors="replace") if fp.is_file() else ""

        ok = normalize(o) == normalize(n)
        if not ok:
            bad = True
        _report(rel, ok, o, n)
        if i < len(paths) - 1:
            print()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
