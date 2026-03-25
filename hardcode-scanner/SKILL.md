---
name: hardcode-scanner
description: |
  检查和清除代码中的业务字段硬编码。当用户提到"硬编码"、"硬编码扫描"、
  "清理硬编码"、"写死了"、"参数化"，或者要求检查代码中是否有特定业务数据
  直接写在代码里时，使用此 skill。也适用于代码审查中发现硬编码需要清理的场景。
---

# 硬编码扫描与清理

## 核心原则

**业务数据的硬编码值只允许存在于 `if __name__ == '__main__'` 块内部，或通过扫描脚本的排除路径明确跳过。**

- "内部"指块本身的直接代码，不包括被 `__main__` 调用的 `main()` 或其他函数
- 函数体、类定义、模块级常量中的业务硬编码都需要参数化上溯到 `__main__` 块或 CLI 入口
- **一次性业务脚本**（如数据导入、格式迁移）不属于核心代码，通过扫描脚本的排除路径跳过，不做修改

## 工作流程

### 1. 确认扫描范围

和用户确认：
- 扫描哪些目录
- 哪些字符串值属于"业务硬编码"（让用户列出具体值）
- 哪些文件类型需要覆盖（`.py`？`.js`/`.jsx`/`.ts`/`.tsx`？）

### 2. 配置扫描脚本

读取 `scripts/scan_hardcoded.py`（与本 SKILL.md 同目录），将其拷贝到任务工作目录。

修改脚本顶部的两个配置区：

- `KNOWN_PATTERNS`：填入用户提供的业务硬编码值
- `EXCLUDE_PATHS`：初始为空，后续根据分析结果添加

配置示例（使用假数据）：
```python
KNOWN_PATTERNS = {
    "school_id": [re.compile(r"""['"]12345['"]""")],
    "school_name": [re.compile(r"""['"]示例大学['"]""")],
}

EXCLUDE_PATHS = [
    "scripts/one_time_import.py",  # 一次性迁移脚本
]
```

### 3. 运行并分析结果

运行脚本，对每个命中按下表分类：

| 命中类型 | 处理方式 |
|---------|---------|
| 函数体内硬编码 | **修复**：提取为函数参数，调用方传入 |
| 函数默认参数 | **修复**：移除默认值，改为必填 |
| `main()` 中的硬编码 | **修复**：main() 加参数，值移到 `if __name__` |
| argparse 默认值 | **修复**：argparse 移到 `if __name__`，main() 接受参数 |
| `.get()` 回退值 | **修复**：移除回退值，让 KeyError 自然抛出 |
| 测试文件 | **排除**：加入 EXCLUDE_PATHS |
| 一次性脚本 | **排除**：加入 EXCLUDE_PATHS |
| mock/示例数据 | **排除或单独任务** |
| 前端 UI 默认值 | **去重**：消除重复定义，集中到一处 |

### 4. 修复代码

**后端参数化上溯模式：**
```python
# 修改前
def process(source_dir):
    params = {"id": "12345"}

# 修改后
def process(source_dir, target_id: str):
    params = {"id": target_id}
```

**main() 硬编码上移模式：**
```python
# 修改前
def main():
    run(target_id='12345')

if __name__ == '__main__':
    main()

# 修改后
def main(target_id: str):
    run(target_id=target_id)

if __name__ == '__main__':
    main(target_id='12345')
```

**前端去重模式：**
```javascript
// 修改前：多个文件重复定义相同默认值
const DEFAULTS = { id: '12345', name: '示例' }

// 修改后：从唯一定义点导入
import { DEFAULTS } from './constants'
```

### 5. 验证

重新运行扫描脚本，确认结果为 **0 命中**。

所有"保留不改"的文件都必须加入 EXCLUDE_PATHS 并带注释，确保输出干净。

## 注意事项

- `main()` 函数体内的硬编码也不允许，即使 `main()` 仅从 `if __name__` 调用
- 前端 UI 默认值可暂时保留（用户体验需要），但必须消除重复定义
- 修改函数签名后，必须检查并同步所有调用方
- EXCLUDE_PATHS 中的每一项都要有注释说明排除原因
