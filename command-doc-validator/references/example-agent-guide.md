# Agent 运行指南

## 快速开始

```bash
cd backend/agent
PYTHONIOENCODING=utf-8 python coordinator_agent.py --indicator "指标名称" --year 2024
```

**重要：**
- 必须设置 `PYTHONIOENCODING=utf-8`，否则会因 emoji 和中文输出导致编码错误
- 在 Claude Code 中统一使用 bash 语法（即使在 Windows 上也用 `PYTHONIOENCODING=utf-8`，不要用 PowerShell 的 `$env:` 语法）

### 完整参数示例

```bash
PYTHONIOENCODING=utf-8 python coordinator_agent.py \
  --indicator "专业专任教师数" \
  --university-id "10701" \
  --university-name "西安电子科技大学" \
  --major-code "080901" \
  --major-name "计算机科学与技术" \
  --year "2024"
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--indicator` | 无 | 指标名称（从指标库查找） |
| `--indicator-file` | 无 | 指标文件路径（.md 格式） |
| `--university-id` | `10701` | 学校编码 |
| `--university-name` | `西安电子科技大学` | 学校名称 |
| `--major-code` | `080901` | 专业代码 |
| `--major-name` | `计算机科学与技术` | 专业名称 |
| `--year` | `2024` | 年份 |
| `--debug` | `False` | 启用调试模式 |

## 交互模式

不传入 `--indicator` 参数时，进入交互模式：

```bash
PYTHONIOENCODING=utf-8 python coordinator_agent.py
```

## 常见问题

### 编码错误

**错误信息：**
```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f4ca'
```

**解决方案：**
```bash
PYTHONIOENCODING=utf-8 python coordinator_agent.py ...
```

### 在 Claude Code 中运行

使用 `timeout=180` 参数，复杂指标可能需要 1-3 分钟：

```bash
cd backend/agent && PYTHONIOENCODING=utf-8 python coordinator_agent.py --indicator "专业专任教师数" --year 2024
```

## 环境要求

- Python 3.12+
- 已设置 `DASHSCOPE_API_KEY` 环境变量
- MCP 服务器运行中
- 指标文件存在于 `data/indicators/` 目录
