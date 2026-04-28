---
name: web-research
description: Use this skill whenever the user asks to search the web, look up current information, fetch web content, compare online sources, summarize a webpage, or investigate something that requires internet access. This skill chooses the fastest available path: WebFetch for known URLs, WebSearch when available for discovery, Playwright Yahoo search as fallback, and Playwright page extraction only when WebFetch cannot read the page.
---

# web-research - 联网搜索与网页抓取混合流程

## 目标

用最快、最稳定的方式完成联网搜索、URL 发现、网页正文提取和结果汇总。

核心策略：

- 已知 URL：直接用 `WebFetch`
- 未知 URL：只尝试一次 `WebSearch`
- `WebSearch` 只要出现一次 0 结果、不可用、报错或超时：立刻放弃 `WebSearch`，不要换关键词重试
- `WebSearch` 不可用或 0 结果：用 `playwright-cli` + Yahoo 搜索找 URL
- 拿到 URL 后：优先切回 `WebFetch` 抓正文
- 只有 `WebFetch` 失败或页面必须 JS 渲染时，才用 Playwright 抓正文

## 决策流程

### 1. 用户提供了 URL

直接使用 `WebFetch`：

```text
WebFetch(url="<用户提供的 URL>", prompt="<具体提取目标>")
```

`prompt` 要写清楚需要提取什么，不要只写“看看这个网页”。

示例：

```text
提取这篇文章中关于 Claude Code 最新版本的新功能、版本号和发布日期。
```

### 2. 用户没有提供 URL，需要搜索

先尝试一次 `WebSearch`。

`WebSearch` 的失败判定很严格：只要出现一次 0 结果（例如 `Did 0 searches`）、不可用、报错或超时，就立刻放弃 `WebSearch`，直接进入 Playwright + Yahoo 搜索流程。不要换关键词重试 `WebSearch`，因为重复 0 结果只会浪费时间。

如果 `WebSearch` 成功：

1. 从搜索结果中选择最权威、最相关的 URL
2. 对这些 URL 使用 `WebFetch` 抓正文
3. 汇总回答
4. 如果使用了 WebSearch，最终回答必须列出来源链接

### 3. WebSearch 不可用或失败

使用 `playwright-cli` 通过 Yahoo 搜索。

推荐命令：

```bash
playwright-cli open "https://search.yahoo.com/search?p=搜索关键词"
playwright-cli eval "document.querySelector('#web')?.innerText?.substring(0, 8000) || document.body.innerText.substring(0, 8000)"
playwright-cli close
```

从搜索结果文本中选择最相关 URL。

选择 URL 时优先级：

1. 官方文档、官方 changelog、官方博客
2. GitHub / release notes / npm / package registry
3. 知名技术媒体
4. 普通博客或聚合站

### 4. 拿到 URL 后抓取正文

优先使用 `WebFetch`，不要继续用 Playwright 抓正文。

```text
WebFetch(url="<搜索得到的 URL>", prompt="提取主要内容、关键结论、版本号、日期和来源依据")
```

这样比 Playwright 更快，也更节省上下文。

### 5. WebFetch 抓取失败

如果 `WebFetch` 返回 unable to fetch、429、空内容或正文不完整，再使用 Playwright 打开页面并提取正文：

```bash
playwright-cli open "https://example.com/article"
playwright-cli eval "document.querySelector('article')?.innerText || document.querySelector('main')?.innerText || document.body.innerText.substring(0, 10000)"
playwright-cli close
```

## Playwright 使用原则

Playwright 是兜底工具，不是默认工具。

适合使用 Playwright 的情况：

- `WebSearch` 不可用，需要搜索
- 页面必须 JS 渲染
- 需要点击、跳转、交互后才能看到内容
- `WebFetch` 抓不到正文

不适合使用 Playwright 的情况：

- 用户已经给了明确 URL
- WebFetch 可以正常抓取
- 只是普通网页正文提取

## 搜索引擎选择

Playwright 搜索默认使用 Yahoo：

```text
https://search.yahoo.com/search?p=关键词
```

原因：

- Google 容易触发验证码
- Bing 在无头浏览器中搜索结果区域经常不稳定
- Yahoo 当前对无头浏览器更稳定

## 输出要求

回答用户时应包含：

1. 直接结论
2. 关键发现
3. 必要时列出版本号、日期、功能点
4. 来源链接或来源说明

如果信息来自 WebSearch，最终回答必须包含：

```markdown
Sources:
- [标题](URL)
```

如果信息来自 Playwright 搜索结果 + WebFetch，也应尽量列出来源 URL。

## 示例流程

### 示例 1：用户给了 URL

用户：

```text
总结这个网页：https://example.com/article
```

执行：

1. 直接 WebFetch
2. 不使用 WebSearch
3. 不使用 Playwright

### 示例 2：用户要求搜索最新信息

用户：

```text
搜索 Claude Code 最新版本有什么新功能
```

执行：

1. 先尝试 WebSearch
2. 如果 WebSearch 不可用，用 Playwright + Yahoo 搜索
3. 拿到官方 changelog URL
4. 用 WebFetch 抓官方 changelog
5. 汇总最新版本功能

### 示例 3：WebFetch 抓不到页面

用户：

```text
帮我看这个动态网页里的内容
```

执行：

1. 先 WebFetch
2. 如果失败，用 Playwright open
3. 用 eval 提取 `article` / `main` / `body.innerText`
4. 汇总内容
