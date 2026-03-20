---
name: diff-noise-check
description: 用本 skill 自带脚本判断 Git 改动是否「只有格式噪声」：空白行增减、Markdown 横线（---/***）、管道表格列对齐、行尾空白；保护 YAML frontmatter 边界。只要用户在问「diff 有没有实质修改」「Obsidian/编辑器保存后是不是只改了格式」「能不能放心提交」「嵌套子仓库怎么比」「和 HEAD 比是不是噪音」、噪声剥离、表格对齐，就应优先读本 skill 并直接运行 scripts/diff_noise_check.py，不要凭肉眼猜。
---

# Diff 噪声检查（diff-noise-check）

## 脚本位置

`.claude/skills/diff-noise-check/scripts/diff_noise_check.py`

（路径相对于本仓库根目录。）

## 你该做什么

1. 在**目标 Git 仓库根目录**打开终端，或用 `--repo` 指向该根目录。
2. Windows 下跑 Python 前建议：`$env:PYTHONIOENCODING='utf-8'`（避免中文输出乱码）。
3. 执行脚本，把终端原文读给用户；**用脚本的结论回答「有没有实质差异」**，不要自己重造一套规则。

## 命令速查

在**本仓库根**执行（嵌套子仓如 `specs` 时用 `--repo` 指向子仓根）：

```powershell
$env:PYTHONIOENCODING='utf-8'; python .claude/skills/diff-noise-check/scripts/diff_noise_check.py --repo specs <相对 specs 的路径>
```

当前目录是**嵌套子仓库根**、且子仓目录在主仓 `specs/` 下时，可用：

```powershell
python ../.claude/skills/diff-noise-check/scripts/diff_noise_check.py
```

（若子仓与主仓的相对路径不同，改成能指到上述 `diff_noise_check.py` 的相对或绝对路径即可。）

常用参数：

| 场景 | 用法 |
|------|------|
| 工作区相对 `HEAD`（默认） | `python .claude/skills/diff-noise-check/scripts/diff_noise_check.py` |
| 只看暂存区 | 加 `--staged` |
| 工作区 vs 暂存区 | 加 `--unstaged` |
| 指定基准提交 | `--base HEAD~1` |
| 只查若干路径 | 路径写在最后 |
| 不用 Git、直接两文件 | `--compare A.md B.md`（勿与 `--repo`/`--staged` 等混用） |

## 如何读输出

- 每个文件两行：**第一行路径**，**第二行**以 `仅噪声` 或 `有实质差异` 开头，制表符后是说明。
- **仅噪声** + 「剥离空白、横线与表格对齐后一致」→ 可视为无实质内容变更（仍应用 `git diff` 自己确认是否要提交格式）。
- **有实质差异** → 剥离噪声后文本仍不同，需按正常代码审阅处理。
- 退出码：`0` 表示所检查项均为「仅噪声」；非 `0` 表示存在「有实质差异」或执行失败。

## 脚本**不会**当成噪声的（易误判点）

- JSON/代码里除「表格行」以外的空格、缩进、字段顺序变化。
- Markdown 非表格行的正文改写。
- 管道表单元格**内部**有意保留的空格（脚本只对 `|` 分割后的单元格做 `strip`，一般与对齐类 diff 一致；若单元格内有多余空格且语义依赖空格，可能仍判为差异——少见）。

## 兼容性

- Python 3、本机已安装 `git`。
- 脚本通过 `git show` / `git diff` 取内容；二进制或未跟踪文件行为与 Git 一致，不另作保证。
