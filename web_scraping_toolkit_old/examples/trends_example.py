#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
示例脚本: 使用 web_scraping_toolkit 进行趋势数据抓取和内容提取
"""

import os
import sys
import json
import time
from datetime import datetime

# 将父目录添加到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added parent directory to PYTHONPATH: {parent_dir}")

# 导入 web_scraping_toolkit 包中的功能
from web_scraping_toolkit import (
    # 趋势模块功能
    get_trend_score_via_serpapi,
    get_trend_score_via_pytrends,
    get_keyword_batch_scores,
    use_fallback_score,
    fetch_weighted_trending_keywords,
    
    # 内容模块功能
    fetch_article_content,
    check_cached_news,
    update_news_cache
)

def test_trends_api():
    """测试 Google Trends API 功能"""
    print("=== 测试 Google Trends API ===")
    
    # 设置环境变量 (可选)
    # os.environ["USE_SERPAPI"] = "true"
    # os.environ["SERPAPI_KEY"] = "your_api_key"
    
    # 1. 测试单个关键词热度获取
    keyword = "Express Entry"
    print(f"\n获取单个关键词 '{keyword}' 的热度...")
    
    # 使用 PyTrends
    print("- 使用 PyTrends API:")
    try:
        score_pytrends = get_trend_score_via_pytrends(keyword)
        print(f"  热度分数: {score_pytrends}")
    except Exception as e:
        print(f"  获取失败: {e}")
    
    # 使用 SerpAPI (如果有 API 密钥)
    if "SERPAPI_KEY" in os.environ:
        print("- 使用 SerpAPI:")
        try:
            score_serpapi = get_trend_score_via_serpapi(keyword)
            print(f"  热度分数: {score_serpapi}")
        except Exception as e:
            print(f"  获取失败: {e}")
    else:
        print("- 跳过 SerpAPI 测试，未设置 SERPAPI_KEY 环境变量")
    
    # 2. 测试批量获取关键词热度
    print("\n批量获取关键词热度...")
    keywords = [
        "Express Entry",
        "Canadian immigration",
        "Study permit Canada",
        "Work permit Canada",
        "Canada PNP"
    ]
    
    start_time = time.time()
    scores = get_keyword_batch_scores(keywords)
    duration = time.time() - start_time
    
    print(f"获取 {len(keywords)} 个关键词的热度，用时 {duration:.2f} 秒")
    for kw, score in scores.items():
        print(f"  {kw}: {score}")
    
    # 3. 测试加权关键词获取
    print("\n获取加权热门关键词...")
    
    # 创建关键词类别字典
    keyword_categories = {
        "签证类别": [
            "Canada immigration", "Express Entry", "PR card", "Study permit"
        ],
        "移民路径": [
            "PNP", "Atlantic Immigration", "Rural Immigration", "Startup visa"
        ],
        "政策和机构": [
            "IRCC", "Immigration Canada", "LMIA", "NOC", "CRS score"
        ]
    }
    
    # 定义高优先级关键词
    priority_keywords = ["Express Entry draw", "CRS cutoff"]
    
    # 定义类别权重
    category_weights = {
        "签证类别": 1.2,
        "移民路径": 1.1,
        "政策和机构": 1.3
    }
    
    # 获取加权后的热门关键词
    weighted_keywords = fetch_weighted_trending_keywords(
        keywords_by_category=keyword_categories,
        priority_keywords=priority_keywords,
        category_weights=category_weights,
        max_keywords=5
    )
    
    print(f"获取到 {len(weighted_keywords)} 个加权热门关键词:")
    for i, kw_data in enumerate(weighted_keywords):
        print(f"  {i+1}. {kw_data['keyword']} (类别: {kw_data['category']}, "
              f"基础分: {kw_data['base_score']}, 加权分: {kw_data['weighted_score']:.2f})")
    
    return scores, weighted_keywords

def test_content_fetching():
    """测试网页内容抓取功能"""
    print("\n=== 测试网页内容抓取 ===")
    
    # 测试文章内容抓取
    url = "https://www.canada.ca/en/immigration-refugees-citizenship/news/notices.html"
    print(f"\n抓取网页内容: {url}")
    
    start_time = time.time()
    content = fetch_article_content(url)
    duration = time.time() - start_time
    
    if content:
        print(f"成功抓取内容，用时 {duration:.2f} 秒")
        # 只显示前200个字符
        preview = content[:200].replace("\n", " ") + "..."
        print(f"内容预览: {preview}")
        print(f"总长度: {len(content)} 字符")
    else:
        print(f"抓取失败，用时 {duration:.2f} 秒")
    
    # 测试缓存功能
    print("\n测试新闻缓存功能:")
    
    # 创建测试新闻数据
    test_news = [
        {
            "title": "测试新闻1",
            "url": "https://example.com/test-news-1",
            "keyword": "Express Entry",
            "source": "测试来源"
        },
        {
            "title": "测试新闻2",
            "url": "https://example.com/test-news-2",
            "keyword": "Immigration Canada",
            "source": "测试来源"
        }
    ]
    
    # 更新缓存
    cache = update_news_cache(test_news)
    print(f"更新缓存后，共有 {len(cache)} 条新闻")
    
    # 检查缓存
    cached_news = check_cached_news()
    print(f"检查缓存: {len(cached_news)} 条新闻")
    
    return content

def save_results(scores, weighted_keywords, output_dir="examples/results"):
    """保存测试结果"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存热度分数
    scores_file = os.path.join(output_dir, f"trend_scores_{timestamp}.json")
    with open(scores_file, "w") as f:
        json.dump(scores, f, indent=2)
    
    # 保存加权关键词
    keywords_file = os.path.join(output_dir, f"weighted_keywords_{timestamp}.json")
    with open(keywords_file, "w") as f:
        json.dump(weighted_keywords, f, indent=2)
    
    print(f"\n结果已保存到: {output_dir}")

if __name__ == "__main__":
    print("=== web_scraping_toolkit 示例脚本 ===")
    print("测试趋势数据抓取和内容提取功能")
    
    # 运行趋势 API 测试
    scores, weighted_keywords = test_trends_api()
    
    # 运行内容抓取测试
    content = test_content_fetching()
    
    # 保存结果
    save_results(scores, weighted_keywords) 