"""
Google Trends 数据抓取模块

提供了多种方法来获取 Google Trends 的趋势数据，包括：
1. SerpAPI 整合
2. PyTrends API
3. 智能后备评分机制
4. 关键词加权和排序
"""

from .trends_api import (
    get_trend_score_via_serpapi,
    get_trend_score_via_pytrends,
    get_keyword_batch_scores,
    use_fallback_score,
    fetch_weighted_trending_keywords
)

__all__ = [
    'get_trend_score_via_serpapi',
    'get_trend_score_via_pytrends',
    'get_keyword_batch_scores',
    'use_fallback_score',
    'fetch_weighted_trending_keywords'
] 