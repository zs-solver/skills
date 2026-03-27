#!/usr/bin/env python3
"""判断改动是否仅为空白、横线、Markdown 表格列对齐。"""
from __future__ import annotations

import argparse
import difflib
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


def normalize_body_fragment(lines: list[str]) -> str:
    """与 normalize() 中非 frontmatter 行相同的归一规则（用于判断 raw 片段是否仅噪声）。"""
    acc: list[str] = []
    for raw in lines:
        s = raw.rstrip("\n\r").rstrip()
        if not s.strip() or _HR.match(s):
            continue
        acc.append(_table_row_norm(s))
    return "\n".join(acc)


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


_MAX_UNIFIED_DIFF_LINES = 120


def _summarize_table_alignment_noise(raw_old: str, raw_new: str) -> str | None:
    """行级 SequenceMatcher：归一化后一致的 replace 块视为表格对齐/空白/横线类 raw 噪声，只统计不打印原文。"""
    a = raw_old.splitlines()
    b = raw_new.splitlines()
    sm = difflib.SequenceMatcher(None, a, b)
    blocks = 0
    raw_line_slots = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "replace":
            continue
        seg_a, seg_b = a[i1:i2], b[j1:j2]
        if not seg_a and not seg_b:
            continue
        if normalize_body_fragment(seg_a) == normalize_body_fragment(seg_b):
            blocks += 1
            raw_line_slots += max(len(seg_a), len(seg_b))
    if blocks == 0:
        return None
    return (
        f"另有 {blocks} 段 raw 差异在「空白/横线/管道表格列对齐」归一化后与基准一致（约 {raw_line_slots} 行），"
        "不展开具体表格或对齐内容"
    )


def _unified_diff_normalized(
    norm_old: str,
    norm_new: str,
    from_label: str,
    to_label: str,
) -> list[str]:
    """剥离噪声后的 unified diff，供人工审阅实质修改。"""
    a = norm_old.splitlines(keepends=False)
    b = norm_new.splitlines(keepends=False)
    lines = list(
        difflib.unified_diff(
            a,
            b,
            fromfile=f"a/{from_label}",
            tofile=f"b/{to_label}",
            lineterm="",
        )
    )
    if len(lines) > _MAX_UNIFIED_DIFF_LINES:
        tail = len(lines) - _MAX_UNIFIED_DIFF_LINES
        lines = lines[:_MAX_UNIFIED_DIFF_LINES] + [f"...（以下省略 {tail} 行）"]
    return lines


def _report(
    rel: str,
    ok: bool,
    raw_old: str,
    raw_new: str,
    *,
    brief: bool,
    diff_from: str | None = None,
    diff_to: str | None = None,
) -> None:
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
    if ok or brief:
        return

    norm_o, norm_n = normalize(raw_old), normalize(raw_new)
    print("  判定思路：全文先做空白/横线剔除与管道表单元格 strip 归一化（frontmatter 行原样保留），比较归一化文本；")
    print("            若仍不同，则输出归一化后的 unified diff 作为实质差异。另用行级 diff 找出「片段归一化后一致」的 replace 块，")
    print("            归为表格对齐类 raw 噪声，仅计数说明、不打印具体表格。")

    noise_hint = _summarize_table_alignment_noise(raw_old, raw_new)
    if noise_hint:
        print(f"  {noise_hint}")

    df = diff_from if diff_from is not None else rel
    dt = diff_to if diff_to is not None else rel
    diff_lines = _unified_diff_normalized(norm_o, norm_n, df, dt)
    print("  剥离噪声后的差异（实质内容，unified diff）：")
    for ln in diff_lines:
        print(f"    {ln}")


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
    ap.add_argument(
        "--brief",
        action="store_true",
        help="有实质差异时也只输出路径与一行结论，不输出判定思路、表格噪声说明与归一化 diff",
    )
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
        _report(
            f"{pa.name} -> {pb.name}",
            ok,
            o,
            n,
            brief=args.brief,
            diff_from=pa.name,
            diff_to=pb.name,
        )
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
        _report(rel, ok, o, n, brief=args.brief)
        if i < len(paths) - 1:
            print()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
