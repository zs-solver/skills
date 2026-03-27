---
name: diff-noise-check
description: 判断 Git 改动在剥离空白、横线、Markdown 管道表格列对齐等之后是否仍有实质差异；支持相对 HEAD、暂存区、工作区及嵌套子仓库等比较方式。适用于用户询问 diff 有无实质修改、保存后是否仅格式变化、表格对齐是否算改动等场景。
---

# Diff 噪声检查

把「看起来像改了很多行」的 diff 压成一句话：**归一化之后，还有没有实质不同**。脚本做确定性归一（空白、横线、表格列对齐等），比人肉扫 diff 稳。

**脚本路径**（相对本仓库根）：`.claude/skills/diff-noise-check/scripts/diff_noise_check.py`

---

## 你要做的事

1. 在**目标 Git 仓库根**执行；若仓库嵌套在主项目里，用 `--repo` 指到那个根（见下）。
2. Windows 下建议先设 `$env:PYTHONIOENCODING='utf-8'`，再跑 Python，避免中文乱码。
3. 跑完后把**终端原文**给用户；**以脚本的「仅噪声 / 有实质差异」为准**，不要自己发明一套噪声定义。

---

## 怎么跑

**主仓库根目录**，查当前工作区相对 `HEAD`：

```powershell
$env:PYTHONIOENCODING='utf-8'; python .claude/skills/diff-noise-check/scripts/diff_noise_check.py
```

**嵌套子仓库**（例如 `specs` 自己是一个 git 仓库）：`--repo` 指向子仓根，后面跟**相对子仓根**的路径：

```powershell
$env:PYTHONIOENCODING='utf-8'; python .claude/skills/diff-noise-check/scripts/diff_noise_check.py --repo specs 路径/到/文件.md
```

已经 `cd` 到子仓根时，也可以不写 `--repo`（脚本会向上找 `.git`）；脚本在别处时，用相对路径指到 `diff_noise_check.py` 即可。

**常用开关**（路径都写在最后；`--compare` 与 git 选项互斥）：

| 目的 | 做法 |
|------|------|
| 工作区 vs `HEAD`（默认） | 不加额外 flag |
| 只看暂存区 | `--staged` |
| 工作区 vs 暂存区 | `--unstaged` |
| 换基准提交 | `--base HEAD~1` 等 |
| 只查若干文件 | 路径列在最后 |
| 两个文件直接比 | `--compare A.md B.md` |
| 有实质差异时只要一行结论 | `--brief`（不打印判定说明和归一化 diff） |

---

## 输出怎么读

- **前两行**：路径；`仅噪声` 或 `有实质差异` + 简短说明。
- **仅噪声**：归一化后一致，通常可当作「没改内容」（是否提交纯格式仍可用 `git diff` 自己定）。
- **有实质差异**（未加 `--brief`）：会多几段——**判定思路**（脚本在做什么）、**表格对齐类噪声的一行统计**（有几段、大约几行 raw，不展开表格原文）、**归一化后的 unified diff**（看实质改了啥；太长会截断）。需要脚本式/一行结果时用 `--brief`。
- **退出码**：`0` 表示检查范围内全是仅噪声；非 `0` 表示有实质差异或执行失败。

---

## 容易误判的点（脚本不会当噪声）

- 普通正文、JSON/代码里**非表格行**的缩进、空格、换行、字段顺序。
- 管道表**单元格内部**有意保留的空格：脚本会对单元格做 strip；若语义依赖空格，少数情况仍会判成差异。

---

## 环境

需要 Python 3 和 `git`。内容来自 `git show` / `git diff`；二进制或未跟踪文件不另做保证。
