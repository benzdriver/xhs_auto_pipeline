"""
内容抓取模块

提供了抓取、处理和缓存网页内容的功能，包括：
1. 抓取文章内容
2. 缓存新闻信息
3. 处理和管理缓存内容
"""

from .content_fetcher import fetch_article_content
from .news_cache import (
    check_cached_news,
    update_news_cache,
    mark_news_processed,
    is_news_cached,
    is_news_processed_by_stage,
    get_unprocessed_news
)

__all__ = [
    'fetch_article_content',
    'check_cached_news',
    'update_news_cache',
    'mark_news_processed',
    'is_news_cached',
    'is_news_processed_by_stage',
    'get_unprocessed_news'
] 