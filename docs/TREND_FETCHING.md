# Google Trends 数据获取指南

本文档介绍如何使用 SerpAPI 和 PyTrends 获取 Google Trends 数据。

## 概述

项目使用多种方法获取 Google Trends 数据，按照优先级顺序：

1. **SerpAPI** (主要方法): 通过 SerpAPI 服务获取趋势数据，能够有效绕过 Google 的反爬虫措施
2. **PyTrends** (后备方法): 如果 SerpAPI 不可用或获取失败，则使用 PyTrends 库直接获取数据
3. **智能后备机制** (最终手段): 当以上方法都失败时，使用预定义的规则和数据估算热度分数

## 配置 SerpAPI

### 获取 SerpAPI 密钥

1. 访问 [SerpAPI](https://serpapi.com/) 注册账号
2. 在账户页面获取 API 密钥

### 设置环境变量

使用以下方式之一设置环境变量：

1. 命令行临时设置：
   ```bash
   export SERPAPI_KEY=your_api_key_here
   export USE_SERPAPI=true
   ```

2. 在 `.env` 文件中永久设置：
   ```
   SERPAPI_KEY=your_api_key_here
   USE_SERPAPI=true
   ```

## 使用方法

### 获取单个关键词趋势分数

```python
from stages.fetch_trends import get_trend_score_via_serpapi

# 获取关键词在加拿大地区的最近7天趋势分数
score = get_trend_score_via_serpapi("Express Entry Canada", geo="CA", timeframe="now 7-d")
print(f"趋势分数: {score}")
```

### 批量获取关键词趋势分数

```python
from stages.fetch_trends import get_keyword_batch_scores

# 定义关键词列表
keywords = [
    "Express Entry",
    "Canadian immigration",
    "Study permit Canada",
    "Work permit Canada",
    "Canada PNP"
]

# 批量获取趋势分数（自动使用SerpAPI、PyTrends或后备机制）
scores = get_keyword_batch_scores(keywords, geo="CA", timeframe="now 7-d")

# 显示结果
for keyword, score in scores.items():
    print(f"{keyword}: {score}")
```

## 测试和验证

使用项目中的测试脚本验证配置：

```bash
# 测试SerpAPI和PyTrends方法（比较结果）
python test_serpapi.py

# 测试完整工作流中的趋势获取
python test_trend_fetching.py
```

## 常见时间范围选项

- `"now 1-H"`: 当前小时
- `"now 4-H"`: 最近4小时
- `"now 1-d"`: 最近1天
- `"now 7-d"`: 最近7天
- `"today 1-m"`: 最近1个月
- `"today 3-m"`: 最近3个月
- `"today 12-m"`: 最近12个月
- `"today 5-y"`: 最近5年
- `"all"`: 所有时间

## 地区代码示例

- `"CA"`: 加拿大
- `"US"`: 美国
- `"GB"`: 英国
- `"AU"`: 澳大利亚
- `"IN"`: 印度
- `"WW"`: 全球

## 后备评分机制

如果 SerpAPI 和 PyTrends 都无法获取数据，系统会使用 `use_fallback_score()` 函数提供一个估计值：

1. 首先检查是否有精确匹配的预定义分数
2. 然后检查是否有部分匹配的关键词
3. 最后根据关键词类别（如移民、签证等）进行智能估计

这确保即使在外部API不可用的情况下，系统也能提供合理的趋势分数估计。 