"""
Web Scraping Toolkit: A comprehensive toolkit for web scraping with proxy rotation,
captcha solving, cache management, and data extraction from various sources.
"""

__version__ = "0.1.0"

# Import main classes to expose at package level
from .proxy.proxy_manager import ProxyManager
from .captcha.captcha_solver import CaptchaSolver
from .cache.cache_mechanism import CacheMechanism
from .scraper import WebScraper

# Import trends module
from .trends import (
    get_trend_score_via_serpapi,
    get_trend_score_via_pytrends,
    get_keyword_batch_scores,
    use_fallback_score,
    fetch_weighted_trending_keywords
)

# Import content module
from .content import (
    fetch_article_content,
    check_cached_news,
    update_news_cache,
    mark_news_processed,
    is_news_cached,
    is_news_processed_by_stage,
    get_unprocessed_news
)

# For easier imports
__all__ = [
    'ProxyManager',
    'CaptchaSolver', 
    'CacheMechanism',
    'WebScraper',
    # Trends module exports
    'get_trend_score_via_serpapi',
    'get_trend_score_via_pytrends',
    'get_keyword_batch_scores',
    'use_fallback_score',
    'fetch_weighted_trending_keywords',
    # Content module exports
    'fetch_article_content',
    'check_cached_news',
    'update_news_cache',
    'mark_news_processed',
    'is_news_cached',
    'is_news_processed_by_stage',
    'get_unprocessed_news',
] 