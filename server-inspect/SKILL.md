---
name: server-inspect
description: |
  通过服务器文件服务和后端 API 远程排查问题、验证功能。
  当需要查看服务器上的真实数据、调用后端接口验证行为、对比本地与服务器差异时使用。
  适用于 bug 排查、功能测试、部署确认等场景。
---

# 远程服务器检查

## 可用能力

### 1. 文件浏览服务

服务器上运行了一个文件浏览服务，可以读取任意文件和目录。

- 查看目录：`curl -s http://{host}:{port}/{path}/`
- 查看文件：`curl -s http://{host}:{port}/{path}`
- 中文路径需要 URL 编码（curl 会自动处理，或手动 percent-encode）

配置位置：`specs/15服务器使用的文件服务.md`

### 2. 后端 API

直接调用服务器后端 API，验证接口行为、查看返回数据。

- 端口和地址在项目根目录 `.env` 中（`BACKEND_HOST` + `BACKEND_PORT`）
- GET 请求：`curl -s "http://{host}:{port}/api/..."`
- POST 请求：`curl -s -X POST -H "Content-Type: application/json" -d '{"key":"value"}' "http://{host}:{port}/api/..."`

## 使用流程

### 获取连接信息

首次使用时，依次读取：

1. `specs/15服务器使用的文件服务.md` — 文件服务地址和端口
2. 通过文件服务读取服务器上的 `.env` — 后端地址和端口

路径参考：`/home/workspace/projects/IndicatorAnalytics/`（服务器上的项目根目录）

### 典型用法

**查看服务器上的数据文件**（注册表、SQL 库、配置等）：
```bash
curl -s "http://{host}:{file_port}/{project_root}/data/indicators_registry.json"
```

**验证接口行为**：
```bash
curl -s "http://{host}:{api_port}/api/library/status/batch?root=@system-preset:校级维度"
```

**对比本地与服务器差异**：
- 用文件服务读服务器文件
- 用本地 Read 工具读本地文件
- 对比关键字段

**用 Python 处理 JSON 数据**（搜索、过滤、统计）：
```bash
PYTHONIOENCODING=utf-8 python -c "
import urllib.request, json
url = 'http://{host}:{file_port}/{path}'
data = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
# ... 分析逻辑
"
```

## 注意事项

- 文件服务是**只读**的，不能修改服务器文件
- API 调用可能产生副作用（POST/DELETE），排查时优先用 GET
- 中文路径在 curl 中可能需要 `--path-as-is` 或手动 URL 编码
- curl 在 Git Bash 中使用 bash 语法，不要用 PowerShell 语法
