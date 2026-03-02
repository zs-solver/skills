---
name: web-fetch
description: 联网获取信息，抓取网页或搜索
argument-hint: [URL或搜索关键词]
---

# web-fetch - 联网获取信息

## 重要提示

**WebSearch 工具在某些环境下不可用**（如使用代理 API 时）。请按以下优先级操作。

## 操作流程

### 1. 用户提供了 URL

直接使用 `WebFetch` 工具：

```
WebFetch(url="https://example.com", prompt="提取主要内容")
```

### 2. 用户未提供 URL（需要搜索）

**先尝试 WebSearch**：
- 如果成功 → 返回搜索结果
- 如果失败（报错、超时、不可用）→ 执行下一步

**WebSearch 不可用时的替代方案**：

告知用户并提供建议：
```
搜索功能当前不可用。你可以：
1. 提供具体网址，我用 WebFetch 抓取
2. 尝试以下常用信息源：
   - AI 新闻: https://www.ithome.com/tag/ai
   - 机器之心: https://www.jiqizhixin.com/
   - TechCrunch AI: https://techcrunch.com/category/artificial-intelligence/
```

### 3. WebFetch 使用要点

- `prompt` 参数要具体描述需要提取的信息
- 可并行请求多个 URL 提高效率
- 遇到 "unable to fetch" 或 429 错误不必重试，换其他源

## prompt 参数示例

```
# 好
"提取这篇文章的主要观点和结论"
"获取产品价格和规格"
"列出最新的新闻标题"

# 差
"看看这个网页" (太模糊)
```

## 常用信息源

| 类型 | URL |
|------|-----|
| AI 资讯 | https://www.ithome.com/tag/ai |
| 机器学习 | https://www.jiqizhixin.com/ |
| 科技新闻 | https://techcrunch.com/ |
| GitHub Trending | https://github.com/trending |
