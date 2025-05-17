# Web Scraping Toolkit

一个功能强大的网页抓取工具包，集成了代理管理、验证码解决、缓存机制和数据提取功能。

## 功能特点

Web Scraping Toolkit 提供了以下主要功能：

### 核心功能

- 代理管理 (ProxyManager)
- 验证码解决 (CaptchaSolver)  
- 缓存机制 (CacheMechanism)
- 基础网页抓取 (WebScraper)

### 趋势数据抓取 (trends 模块)

提供了多种方法获取 Google Trends 的热度数据：

- **SerpAPI 集成**: 通过第三方 API 服务获取 Google Trends 数据
- **PyTrends 集成**: 使用官方 Python 库获取 Google Trends 数据
- **批量处理**: 批量获取多个关键词的热度数据
- **智能后备**: 当 API 不可用时提供智能估算值
- **加权关键词**: 基于类别和优先级的关键词加权和排序

### 内容抓取 (content 模块)

提供了抓取和管理新闻文章内容的工具：

- **内容抓取**: 使用 Playwright 抓取动态渲染的网页内容
- **内容解析**: 使用 BeautifulSoup 解析静态网页内容
- **新闻缓存**: 缓存新闻文章，避免重复处理
- **状态管理**: 跟踪处理状态，记录已处理和未处理的内容

## 安装

```bash
# 从源代码安装
pip install -e .

# 或直接安装依赖
pip install -r requirements.txt
```

## 使用示例

### 趋势数据抓取

```python
from web_scraping_toolkit import get_trend_score_via_pytrends

# 获取单个关键词的热度分数
score = get_trend_score_via_pytrends("Express Entry")
print(f"热度分数: {score}")

# 批量获取多个关键词的热度分数
from web_scraping_toolkit import get_keyword_batch_scores

keywords = ["Express Entry", "Canada immigration", "Study permit"]
scores = get_keyword_batch_scores(keywords)

for kw, score in scores.items():
    print(f"{kw}: {score}")
```

### 加权关键词排序

```python
from web_scraping_toolkit import fetch_weighted_trending_keywords

# 定义关键词类别
keyword_categories = {
    "签证类别": ["Express Entry", "PR card", "Study permit"],
    "移民路径": ["PNP", "Atlantic Immigration", "Startup visa"]
}

# 定义高优先级关键词
priority_keywords = ["Express Entry draw", "CRS cutoff"]

# 获取加权排序后的关键词
weighted_keywords = fetch_weighted_trending_keywords(
    keywords_by_category=keyword_categories,
    priority_keywords=priority_keywords,
    max_keywords=5
)
```

### 内容抓取

```python
from web_scraping_toolkit import fetch_article_content

# 抓取文章内容
url = "https://example.com/article"
content = fetch_article_content(url)
print(content[:200] + "...")  # 预览前200个字符
```

### 新闻缓存

```python
from web_scraping_toolkit import (
    check_cached_news,
    update_news_cache,
    mark_news_processed
)

# 更新新闻缓存
news_items = [
    {"title": "标题1", "url": "https://example.com/1", "keyword": "关键词1"},
    {"title": "标题2", "url": "https://example.com/2", "keyword": "关键词2"}
]
update_news_cache(news_items)

# 标记新闻已处理
mark_news_processed("https://example.com/1", "content_generation")

# 获取未处理的新闻
from web_scraping_toolkit import get_unprocessed_news
unprocessed = get_unprocessed_news("content_generation")
```

## 详细文档

查看 `examples` 目录中的示例代码了解更多用法。

## Features

- **Smart Proxy Management**: Rotate between multiple proxies, detect failures, and avoid IP bans
- **Captcha Handling**: Integrate with services like 2Captcha to solve CAPTCHAs automatically
- **Browser Automation**: Use Playwright for advanced browser-based scraping
- **Cache Management**: Efficient caching system to avoid redundant requests
- **Error Resilience**: Multiple fallback strategies when primary scraping methods fail

## Installation

```bash
pip install web-scraping-toolkit
```

## Basic Usage

```python
from web_scraping_toolkit import ProxyManager, CacheMechanism, WebScraper

# Initialize the proxy manager
proxy_manager = ProxyManager()

# Initialize the cache system
cache = CacheMechanism("my_scraping_cache")

# Create a scraper with automatic proxy rotation
scraper = WebScraper(
    proxy_manager=proxy_manager,
    cache_mechanism=cache
)

# Fetch a web page with automatic proxy rotation and caching
response = scraper.get("https://example.com")
```

## Advanced Usage

### Proxy Rotation

```python
from web_scraping_toolkit import ProxyManager

# Create a proxy manager with custom settings
proxy_manager = ProxyManager(
    rotation_interval=300,  # Rotate every 5 minutes
    max_requests_per_ip=10  # Max 10 requests per IP before rotation
)

# Get a proxy for use with requests
proxy = proxy_manager.get_proxy()

# Mark current proxy as bad (e.g., if it gets blocked)
proxy_manager.blacklist_current_proxy(duration_minutes=30)

# Get a proxy specifically formatted for Playwright
playwright_proxy = proxy_manager.get_playwright_proxy()
```

### Captcha Solving

```python
from web_scraping_toolkit import CaptchaSolver

# Initialize with your 2Captcha API key
solver = CaptchaSolver(api_key="your_2captcha_api_key")

# Solve a reCAPTCHA
solution = solver.solve_recaptcha(
    site_key="6LcXXXXXXXXXXXXXXXXXXXXX",
    page_url="https://example.com"
)

# Use with Playwright
def handle_page_with_captcha(page):
    if solver.detect_and_solve_recaptcha(page):
        print("Captcha solved successfully!")
```

### Cache Management

```python
from web_scraping_toolkit import CacheMechanism

# Initialize cache with a specific name
cache = CacheMechanism("news_scraper_cache")

# Check if an item is in cache
if cache.is_cached("https://example.com/article-1"):
    # Get cached data
    data = cache.get_cached_data("https://example.com/article-1")
else:
    # Fetch and cache new data
    data = fetch_new_data()
    cache.cache_data("https://example.com/article-1", data)

# Mark an item as processed
cache.mark_as_processed("https://example.com/article-1", stage="content_extraction")

# Get unprocessed items
unprocessed = cache.get_unprocessed_items(stage="content_extraction")
```

## Configuration

The toolkit supports configuration via environment variables or a `.env` file:

```
# .env file example
USE_PROXY=true
PROXY_ROTATION_INTERVAL=300
SMARTPROXY_USERNAME=user
SMARTPROXY_PASSWORD=pass
SMARTPROXY_ENDPOINT=gate.smartproxy.com
SMARTPROXY_PORT=7000
TWOCAPTCHA_API_KEY=your_key
```

## License

MIT 