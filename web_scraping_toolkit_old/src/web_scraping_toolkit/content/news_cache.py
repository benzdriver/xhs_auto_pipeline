"""
新闻缓存管理工具

提供了用于管理和操作新闻缓存的工具，支持：
1. 检查缓存的新闻
2. 更新缓存
3. 标记处理状态
4. 获取未处理的新闻
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# 配置日志
logger = logging.getLogger("web_scraping_toolkit.content")

class NewsCacheManager:
    """新闻缓存管理类"""
    
    def __init__(self, cache_dir: str = "data", cache_filename: str = "news_cache.json"):
        """
        初始化新闻缓存管理器
        
        Args:
            cache_dir: 缓存目录
            cache_filename: 缓存文件名
        """
        self.cache_dir = cache_dir
        self.cache_filename = cache_filename
        self.cache_path = os.path.join(cache_dir, cache_filename)
    
    def load_cache(self) -> Dict[str, Any]:
        """加载缓存数据"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取新闻缓存失败: {e}")
                return {}
        return {}
    
    def save_cache(self, cache_data: Dict[str, Any]) -> None:
        """保存缓存数据"""
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    def is_cached(self, url: str, cache_data: Optional[Dict[str, Any]] = None) -> bool:
        """检查URL是否已缓存"""
        if cache_data is None:
            cache_data = self.load_cache()
        
        news_id = hashlib.md5(url.encode()).hexdigest()
        return news_id in cache_data
    
    def is_processed_by_stage(
        self, 
        url: str, 
        stage_name: str, 
        cache_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查新闻是否已被特定阶段处理"""
        if cache_data is None:
            cache_data = self.load_cache()
        
        news_id = hashlib.md5(url.encode()).hexdigest()
        if news_id in cache_data:
            processed_stages = cache_data[news_id].get("processed_stages", [])
            return stage_name in processed_stages
        return False
    
    def mark_processed(self, url: str, stage_name: str) -> bool:
        """标记新闻已被某个阶段处理"""
        cache_data = self.load_cache()
        
        news_id = hashlib.md5(url.encode()).hexdigest()
        if news_id in cache_data:
            if "processed_stages" not in cache_data[news_id]:
                cache_data[news_id]["processed_stages"] = []
                
            if stage_name not in cache_data[news_id]["processed_stages"]:
                cache_data[news_id]["processed_stages"].append(stage_name)
                cache_data[news_id]["last_processed"] = datetime.now().isoformat()
                
                # 写回缓存
                self.save_cache(cache_data)
                return True
        return False
    
    def update_cache(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新缓存数据"""
        cache_data = self.load_cache()
        now = datetime.now().isoformat()
        
        # 添加新新闻到缓存
        for item in news_items:
            news_id = hashlib.md5(item["url"].encode()).hexdigest()
            if news_id not in cache_data:
                cache_data[news_id] = {
                    "title": item["title"],
                    "url": item["url"],
                    "first_seen": now,
                    "keyword": item.get("keyword", ""),
                    "source": item.get("source", ""),
                    "processed_stages": []  # 初始化已处理阶段列表
                }
        
        self.save_cache(cache_data)
        return cache_data
    
    def get_unprocessed_news(self, stage_name: str) -> List[Dict[str, Any]]:
        """获取尚未被特定阶段处理的新闻"""
        cache_data = self.load_cache()
        
        unprocessed = []
        for news_id, info in cache_data.items():
            if stage_name not in info.get("processed_stages", []):
                # 复制基本信息
                item = {
                    "url": info["url"],
                    "title": info["title"],
                    "first_seen": info["first_seen"],
                }
                
                # 添加可选字段
                for field in ["keyword", "source", "type", "category", "score"]:
                    if field in info:
                        item[field] = info[field]
                
                unprocessed.append(item)
        
        return unprocessed

# 为了方便直接调用，创建一个全局实例
_default_cache_manager = NewsCacheManager()

# 外部接口函数，使用全局实例
def check_cached_news() -> Dict[str, Any]:
    """检查本地缓存的新闻，避免重复处理"""
    return _default_cache_manager.load_cache()

def update_news_cache(news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """更新本地缓存的新闻"""
    return _default_cache_manager.update_cache(news_items)

def mark_news_processed(url: str, stage_name: str) -> bool:
    """标记新闻已被某个阶段处理"""
    return _default_cache_manager.mark_processed(url, stage_name)

def is_news_cached(url: str, cached_news: Optional[Dict[str, Any]] = None) -> bool:
    """检查新闻是否已被缓存过"""
    return _default_cache_manager.is_cached(url, cached_news)

def is_news_processed_by_stage(
    url: str, 
    stage_name: str, 
    cached_news: Optional[Dict[str, Any]] = None
) -> bool:
    """检查新闻是否已被特定阶段处理过"""
    return _default_cache_manager.is_processed_by_stage(url, stage_name, cached_news)

def get_unprocessed_news(stage_name: str) -> List[Dict[str, Any]]:
    """获取尚未被特定阶段处理的新闻"""
    return _default_cache_manager.get_unprocessed_news(stage_name) 