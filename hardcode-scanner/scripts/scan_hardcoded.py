"""
业务字段硬编码扫描脚本

扫描指定目录中的业务字段硬编码，输出分类报告。
使用前需配置顶部的 KNOWN_PATTERNS 和 EXCLUDE_PATHS。

用法：
    python scan_hardcoded.py [目录1] [目录2] ...
    不指定目录时，默认扫描项目根目录下的 backend/ 和 frontend/src/
"""

import ast
import re
import sys
from pathlib import Path
from dataclasses import dataclass


# ============================================================
# 配置区：排除路径（相对于项目根目录，每项带注释说明原因）
# ============================================================

EXCLUDE_PATHS: list[str] = [
    # "path/to/one_time_script.py",  # 一次性脚本，不再维护
]

# ============================================================
# 配置区：检测模式（按业务字段分组，值用正则匹配引号包裹的字面量）
# ============================================================

KNOWN_PATTERNS: dict[str, list[re.Pattern]] = {
    # "field_name": [
    #     re.compile(r"""['"]hardcoded_value['"]"""),
    # ],
}

# ============================================================
# 以下为扫描引擎，通常不需要修改
# ============================================================

PYTHON_EXTENSIONS = {".py"}
JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}
ALL_EXTENSIONS = PYTHON_EXTENSIONS | JS_EXTENSIONS


@dataclass
class Hit:
    file: str
    line_no: int
    field_type: str
    matched_value: str
    context: str
    location_type: str


def should_exclude_file(filepath: Path, project_root: Path) -> bool:
    rel = filepath.relative_to(project_root)
    rel_posix = rel.as_posix()

    for part in rel.parts:
        if part in ("test", "tests", "__pycache__"):
            return True

    if filepath.name.startswith("test_") and filepath.suffix == ".py":
        return True

    for excluded in EXCLUDE_PATHS:
        if rel_posix.endswith(excluded) or rel_posix == excluded:
            return True

    return False


def get_if_main_ranges(source: str) -> list[tuple[int, int]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    ranges = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare) or len(test.comparators) != 1:
            continue

        left = test.left
        comp = test.comparators[0]

        is_name_main = (
            (isinstance(left, ast.Name) and left.id == "__name__"
             and isinstance(comp, ast.Constant) and comp.value == "__main__")
            or
            (isinstance(comp, ast.Name) and comp.id == "__name__"
             and isinstance(left, ast.Constant) and left.value == "__main__")
        )

        if is_name_main:
            ranges.append((node.lineno, node.end_lineno or node.lineno))

    return ranges


def get_docstring_ranges(source: str) -> list[tuple[int, int]]:
    ranges = []
    for m in re.finditer(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', source):
        start_line = source[:m.start()].count('\n') + 1
        end_line = source[:m.end()].count('\n') + 1
        ranges.append((start_line, end_line))
    return ranges


def in_any_range(line_no: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= line_no <= end for start, end in ranges)


def is_comment_line(line: str, is_python: bool) -> bool:
    stripped = line.lstrip()
    if is_python:
        return stripped.startswith('#')
    return stripped.startswith('//')


def classify_location(line: str) -> str:
    stripped = line.strip()
    if re.match(r'def\s+\w+\s*\(', stripped):
        return "函数默认参数"
    if '.get(' in stripped:
        return ".get() 回退值"
    if 'Query(' in stripped or 'Path(' in stripped:
        return "API 参数默认值"
    if '=' in stripped and not stripped.startswith(('if ', 'elif ', 'return')):
        lhs = stripped.split('=')[0].strip().rstrip(':').strip()
        if lhs and lhs.replace('_', '').isupper():
            return "模块级常量"
        return "变量赋值"
    if 'return' in stripped:
        return "返回值"
    return "函数体内"


def scan_file(filepath: Path, project_root: Path) -> list[Hit]:
    try:
        source = filepath.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return []

    is_python = filepath.suffix in PYTHON_EXTENSIONS
    lines = source.splitlines()

    exclude_ranges: list[tuple[int, int]] = []
    if is_python:
        exclude_ranges.extend(get_if_main_ranges(source))
        exclude_ranges.extend(get_docstring_ranges(source))

    hits = []
    rel_path = filepath.relative_to(project_root).as_posix()

    for line_no, line in enumerate(lines, 1):
        if in_any_range(line_no, exclude_ranges):
            continue
        if is_comment_line(line, is_python):
            continue

        for field_type, patterns in KNOWN_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    hits.append(Hit(
                        file=rel_path,
                        line_no=line_no,
                        field_type=field_type,
                        matched_value=match.group(0),
                        context=line.rstrip(),
                        location_type=classify_location(line),
                    ))

    return hits


def scan_directory(directory: Path, project_root: Path) -> list[Hit]:
    all_hits = []
    for filepath in sorted(directory.rglob('*')):
        if not filepath.is_file():
            continue
        if filepath.suffix not in ALL_EXTENSIONS:
            continue
        if should_exclude_file(filepath, project_root):
            continue
        all_hits.extend(scan_file(filepath, project_root))
    return all_hits


def print_report(hits: list[Hit], scanned_dirs: list[str]) -> None:
    print(f"扫描目录: {', '.join(scanned_dirs)}\n")

    if not hits:
        print("✅ 未发现业务字段硬编码。")
        return

    by_field: dict[str, list[Hit]] = {}
    for h in hits:
        by_field.setdefault(h.field_type, []).append(h)

    print(f"共发现 {len(hits)} 处硬编码\n")

    for field_type, field_hits in by_field.items():
        print(f"{'=' * 60}")
        print(f"  {field_type}（{len(field_hits)} 处）")
        print(f"{'=' * 60}")
        for i, h in enumerate(field_hits, 1):
            print(f"  #{i}  {h.file}:{h.line_no}")
            print(f"      值: {h.matched_value}")
            print(f"      类型: {h.location_type}")
            print(f"      上下文: {h.context.strip()}")
            print()

    by_file: dict[str, list[Hit]] = {}
    for h in hits:
        by_file.setdefault(h.file, []).append(h)

    print(f"\n{'=' * 60}")
    print("  按文件汇总")
    print(f"{'=' * 60}")
    for filepath, file_hits in sorted(by_file.items()):
        field_types = sorted(set(h.field_type for h in file_hits))
        print(f"  {filepath}: {len(file_hits)} 处 ({', '.join(field_types)})")


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parents[4]

    scan_targets = [
        project_root / "backend",
        project_root / "frontend" / "src",
    ]

    if len(sys.argv) > 1:
        scan_targets = [Path(p) for p in sys.argv[1:]]

    for target in scan_targets:
        if not target.is_dir():
            print(f"错误: 目录不存在: {target}", file=sys.stderr)
            sys.exit(1)

    all_hits: list[Hit] = []
    dir_names: list[str] = []
    for target in scan_targets:
        all_hits.extend(scan_directory(target, project_root))
        dir_names.append(str(target.relative_to(project_root)))

    print_report(all_hits, dir_names)
