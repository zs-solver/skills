---
name: delete-nul
description: 删除 Windows 上的 nul 保留名文件。当用户需要删除名为 nul 的文件（通常是意外创建的 Windows 保留设备名）时使用此技能。
---

# 删除 nul 文件

## 背景

在 Windows 上，`nul` 是保留的设备名称（类似 Linux 的 `/dev/null`），常规删除方法可能失败。

## 删除方法

使用 `rm -f` 命令（Git Bash 环境）：

```bash
rm -f "路径/nul"
```

示例：
```bash
rm -f "C:/Users/zs/Documents/code/project/nul"
```

## 注意事项

- 使用正斜杠 `/` 或转义的反斜杠
- 路径建议用引号包裹
