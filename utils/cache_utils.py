#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存工具类 - 使用 web_scraping_toolkit 中的缓存功能
"""

import os
import json
from datetime import datetime

# 导入 web_scraping_toolkit 中的缓存功能
from web_scraping_toolkit.content import (
    check_cached_news as wst_check_cached_news,
    mark_news_processed as wst_mark_news_processed,
    is_news_processed_by_stage as wst_is_news_processed_by_stage,
    get_unprocessed_news as wst_get_unprocessed_news
)

def check_cached_news():
    """检查本地缓存的新闻，避免重复处理
    
    委托给 web_scraping_toolkit 中的实现
    """
    return wst_check_cached_news()

def mark_news_processed(url, stage_name):
    """标记新闻已被某个阶段处理
    
    委托给 web_scraping_toolkit 中的实现
    """
    return wst_mark_news_processed(url, stage_name)

def is_news_processed_by_stage(url, stage_name):
    """检查新闻是否已被特定阶段处理过
    
    委托给 web_scraping_toolkit 中的实现
    """
    return wst_is_news_processed_by_stage(url, stage_name)

def get_unprocessed_news(stage_name):
    """获取尚未被特定阶段处理的新闻
    
    这里有特定于项目的逻辑，但底层使用工具包的实现
    """
    # 调用工具包的函数获取未处理新闻
    unprocessed = wst_get_unprocessed_news(stage_name)
    
    # 如果工具包返回了内容，直接返回
    if unprocessed:
        return unprocessed
    
    # 否则，使用原有逻辑
    news_content_path = "data/news_content.json"
    result = []
    
    if os.path.exists(news_content_path):
        try:
            with open(news_content_path, "r") as f:
                news_content = json.load(f)
                
                # 检查相应阶段的输出文件是否存在
                output_exists = True
                if stage_name == "generate_content":
                    output_exists = os.path.exists("data/generated_content.json")
                elif stage_name == "generate_image":
                    output_exists = os.path.exists("data/image_content.json")
                
                for item in news_content:
                    url = item.get("url", "")
                    if url:
                        # 如果输出文件不存在或者该新闻未被处理，则加入未处理列表
                        if not output_exists or not is_news_processed_by_stage(url, stage_name):
                            result.append(item)
        except Exception as e:
            print(f"[WARN] 读取新闻内容文件失败: {e}")
    
    return result

# 保留一些特定于项目的函数，但内部使用工具包的实现
def mark_batch_processed(news_list, stage_name):
    """批量标记新闻为已处理"""
    for news in news_list:
        url = news.get("url", "")
        if url:
            mark_news_processed(url, stage_name)

def reset_stage_processing(stage_name):
    """重置某个阶段的处理状态，使所有新闻都被视为未处理
    
    注意：此功能在工具包中尚未实现，保留原始实现
    """
    cache_path = "data/news_cache.json"
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                cached = json.load(f)
                
            # 从所有新闻的处理阶段列表中移除指定阶段
            modified = False
            for news_id, news_info in cached.items():
                if "processed_stages" in news_info and stage_name in news_info["processed_stages"]:
                    news_info["processed_stages"].remove(stage_name)
                    modified = True
            
            # 如果有修改，写回缓存
            if modified:
                with open(cache_path, "w") as f:
                    json.dump(cached, f, ensure_ascii=False, indent=2)
                print(f"[INFO] 已重置阶段 '{stage_name}' 的处理状态")
                return True
                
        except Exception as e:
            print(f"[ERROR] 重置阶段处理状态失败: {e}")
    
    return False 