"""
Google Trends 数据获取 API

封装了多种获取 Google Trends 数据的方法：
1. SerpAPI - 通过第三方 API 服务获取数据
2. PyTrends - 通过官方库获取数据
3. 智能后备分数 - 当 API 不可用时提供估算值
"""

import os
import json
import time
import random
import logging
import requests
from typing import Dict, List, Union, Optional
from pytrends.request import TrendReq

# 配置日志
logger = logging.getLogger("web_scraping_toolkit.trends")

# 默认配置
DEFAULT_GEO = "CA"  # 默认地区：加拿大
DEFAULT_TIMEFRAME = "now 7-d"  # 默认时间范围：最近7天

# 默认后备分数数据库
DEFAULT_SCORES = {
    "Express Entry": 85,
    "Express Entry draw": 90,
    "Canada immigration": 80,
    "Canadian immigration": 83, 
    "PR card": 65,
    "Express Entry draw": 90, 
    "CRS cutoff": 85,
    "IRCC announcement": 75,
    "PR processing time": 82,
    "Immigration policy change": 70,
    "Study permit": 75,
    "Work permit": 78,
    "Study permit Canada": 76,
    "Visitor visa": 63,
    "Family sponsorship": 58,
    "Super visa": 45,
    "PGWP": 67,
    "Open work permit": 72,
    "Canada PNP": 73,
    "PNP": 70,
    "Ontario PNP": 71,
    "BC PNP": 69,
}

def get_trend_score_via_serpapi(
    keyword: str, 
    geo: str = DEFAULT_GEO, 
    timeframe: str = DEFAULT_TIMEFRAME,
    api_key: Optional[str] = None
) -> int:
    """
    通过 SerpAPI 获取 Google Trends 数据
    
    Args:
        keyword: 要查询的关键词
        geo: 地区代码，如 "CA" 为加拿大
        timeframe: 时间范围，如 "now 7-d" 为最近7天
        api_key: SerpAPI 密钥，如未提供则从环境变量获取
        
    Returns:
        趋势分数 (0-100 整数)
    """
    try:
        # 获取 SerpAPI 密钥
        api_key = api_key or os.environ.get("SERPAPI_KEY")
        
        if not api_key:
            logger.warning("未设置 SerpAPI 密钥，无法使用 SerpAPI 获取 Google Trends 数据")
            return use_fallback_score(keyword)
        
        logger.info(f"通过 SerpAPI 获取关键词 '{keyword}' 的趋势数据")
        
        # 构建请求参数
        params = {
            "engine": "google_trends",
            "q": keyword,
            "geo": geo,
            "date": timeframe,
            "api_key": api_key
        }
        
        # 发送请求
        response = requests.get("https://serpapi.com/search", params=params)
        
        # 检查响应状态
        if response.status_code != 200:
            logger.warning(f"SerpAPI 请求失败: 状态码 {response.status_code}")
            return use_fallback_score(keyword)
        
        # 解析响应
        data = response.json()
        
        # 尝试从不同位置提取趋势分数
        if "interest_over_time" in data and data["interest_over_time"].get("timeline_data"):
            timeline_data = data["interest_over_time"]["timeline_data"]
            values = []
            
            # 提取时间线数据中的值
            for point in timeline_data:
                if "values" in point:
                    for value_data in point["values"]:
                        if value_data.get("query") == keyword and "value" in value_data:
                            try:
                                value = int(value_data["value"])
                                values.append(value)
                            except (ValueError, TypeError):
                                pass
            
            # 计算平均值
            if values:
                avg_value = sum(values) / len(values)
                logger.info(f"SerpAPI 成功获取趋势分数: {avg_value:.1f}")
                return int(avg_value)
        
        # 检查是否有替代数据结构
        if "interest_over_time" in data and "averages" in data["interest_over_time"]:
            averages = data["interest_over_time"]["averages"]
            if keyword in averages:
                value = averages[keyword]
                logger.info(f"SerpAPI 成功获取平均趋势分数: {value}")
                return int(value)
        
        logger.warning("无法从 SerpAPI 响应中提取趋势分数")
        return use_fallback_score(keyword)
        
    except Exception as e:
        logger.error(f"SerpAPI 请求过程中出错: {e}")
        return use_fallback_score(keyword)

def get_trend_score_via_pytrends(
    keyword: str, 
    geo: str = DEFAULT_GEO, 
    timeframe: str = DEFAULT_TIMEFRAME
) -> int:
    """
    通过 PyTrends 库获取 Google Trends 数据
    
    Args:
        keyword: 要查询的关键词
        geo: 地区代码，如 "CA" 为加拿大
        timeframe: 时间范围，如 "now 7-d" 为最近7天
        
    Returns:
        趋势分数 (0-100 整数)
    """
    try:
        logger.info(f"通过 PyTrends 获取关键词 '{keyword}' 的趋势数据")
        
        # 初始化 PyTrends
        pytrends = TrendReq(hl='en-CA', tz=360)
        
        # 构建请求
        pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
        
        # 获取数据
        data = pytrends.interest_over_time()
        
        # 提取分数
        if not data.empty and keyword in data:
            score = int(data[keyword].mean())
            logger.info(f"PyTrends 成功获取趋势分数: {score}")
            return score
        else:
            logger.warning("PyTrends 返回了空数据")
            return use_fallback_score(keyword)
    except Exception as e:
        logger.error(f"PyTrends 请求过程中出错: {e}")
        return use_fallback_score(keyword)

def use_fallback_score(keyword: str) -> int:
    """
    当所有获取方法都失败时，使用预定义的分数作为后备
    
    Args:
        keyword: 要获取分数的关键词
        
    Returns:
        估算的趋势分数 (0-100 整数)
    """
    # 检查完全匹配
    if keyword in DEFAULT_SCORES:
        score = DEFAULT_SCORES[keyword] + random.uniform(-3, 3)
        logger.info(f"使用预定义后备数据，完全匹配键: '{keyword}', 分数: {score:.1f}")
        return int(score)
    
    # 检查部分匹配
    for k, v in DEFAULT_SCORES.items():
        if k.lower() in keyword.lower() or keyword.lower() in k.lower():
            score = v + random.uniform(-5, 5)
            logger.info(f"使用预定义后备数据，部分匹配 '{k}' ⊂ '{keyword}', 分数: {score:.1f}")
            return int(score)
    
    # 类别估计
    if any(k in keyword.lower() for k in ['express entry', 'express', 'entry']):
        score = random.randint(80, 90)  # 最热门移民项目
    elif any(k in keyword.lower() for k in ['immigration', 'immigrant', 'canada']):
        score = random.randint(70, 85)  # 移民/加拿大相关
    elif any(k in keyword.lower() for k in ['visa', 'permit', 'pr']):
        score = random.randint(65, 80)  # 签证/许可
    elif any(k in keyword.lower() for k in ['pnp', 'provincial', 'ontario', 'bc', 'alberta']):
        score = random.randint(60, 75)  # 省份项目
    elif any(k in keyword.lower() for k in ['work', 'study', 'student']):
        score = random.randint(60, 75)  # 工作/学习
    else:
        score = random.randint(40, 60)  # 其他关键词
    
    logger.info(f"使用类别估算值: {score}")
    return score

def get_keyword_batch_scores(
    keywords: List[str], 
    geo: str = DEFAULT_GEO, 
    timeframe: str = DEFAULT_TIMEFRAME,
    use_serpapi: Optional[bool] = None,
    serpapi_key: Optional[str] = None
) -> Dict[str, int]:
    """
    批量获取关键词的热度分数
    
    优先使用 SerpAPI，然后是 PyTrends API，最后使用后备评分机制
    
    Args:
        keywords: 要查询的关键词列表
        geo: 地区代码，如 "CA" 为加拿大
        timeframe: 时间范围，如 "now 7-d" 为最近7天
        use_serpapi: 是否使用 SerpAPI，如未提供则从环境变量获取
        serpapi_key: SerpAPI 密钥，如未提供则从环境变量获取
        
    Returns:
        关键词和趋势分数的字典
    """
    scores = {}
    
    # 确定是否使用 SerpAPI
    if use_serpapi is None:
        use_serpapi = os.environ.get("USE_SERPAPI", "").lower() == "true"
    
    # 第一步：尝试使用 SerpAPI 获取数据
    if use_serpapi:
        logger.info("使用 SerpAPI 获取趋势数据")
        for kw in keywords:
            try:
                score = get_trend_score_via_serpapi(kw, geo, timeframe, api_key=serpapi_key)
                scores[kw] = score
                logger.info(f"成功获取关键词 '{kw}' 的趋势分数: {score} (via SerpAPI)")
                time.sleep(1)  # 添加适当延迟，避免 API 限制
            except Exception as e:
                logger.warning(f"SerpAPI 获取 '{kw}' 失败: {e}")
                # 不急着使用后备方法，先继续处理其他关键词
                scores[kw] = None  # 标记为待处理
    
    # 第二步：对于没有成功获取到数据的关键词，尝试使用 PyTrends
    missing_keywords = [kw for kw in keywords if kw not in scores or scores[kw] is None]
    if missing_keywords:
        logger.info(f"尝试使用 PyTrends API 获取剩余 {len(missing_keywords)} 个关键词的数据")
        try:
            pytrends = TrendReq(hl='en-CA', tz=360)
            batch_size = 5  # Google Trends API 限制
            
            for i in range(0, len(missing_keywords), batch_size):
                batch = missing_keywords[i:i+batch_size]
                try:
                    pytrends.build_payload(batch, timeframe=timeframe, geo=geo)
                    data = pytrends.interest_over_time()
                    if not data.empty:
                        for kw in batch:
                            if kw in data:
                                api_score = int(data[kw].mean())
                                logger.info(f"成功获取关键词 '{kw}' 的趋势分数: {api_score} (via PyTrends)")
                                scores[kw] = api_score
                    time.sleep(2)  # 添加适当延迟，避免被阻止
                except Exception as e:
                    logger.warning(f"PyTrends API 查询批次 {batch} 失败: {e}")
        except Exception as e:
            logger.warning(f"PyTrends API 初始化失败: {e}")
    
    # 第三步：对仍未获取到数据的关键词使用后备分数
    final_missing = [kw for kw in keywords if kw not in scores or scores[kw] is None]
    for kw in final_missing:
        fallback_score = use_fallback_score(kw)
        logger.info(f"使用后备分数为关键词 '{kw}': {fallback_score}")
        scores[kw] = fallback_score
    
    return scores 

def fetch_weighted_trending_keywords(
    keywords_by_category: Dict[str, List[str]],
    priority_keywords: List[str] = None,
    category_weights: Dict[str, float] = None,
    max_keywords: int = 10,
    geo: str = DEFAULT_GEO,
    timeframe: str = DEFAULT_TIMEFRAME,
    use_serpapi: Optional[bool] = None,
    serpapi_key: Optional[str] = None
) -> List[Dict]:
    """
    获取加权后的热门关键词
    
    Args:
        keywords_by_category: 按类别分组的关键词字典
        priority_keywords: 高优先级关键词列表（无论热度如何，都会优先考虑）
        category_weights: 各类别的权重
        max_keywords: 返回的最大关键词数量
        geo: 地区代码，如 "CA" 为加拿大
        timeframe: 时间范围，如 "now 7-d" 为最近7天
        use_serpapi: 是否使用 SerpAPI，如未提供则从环境变量获取
        serpapi_key: SerpAPI 密钥，如未提供则从环境变量获取
        
    Returns:
        加权排序后的关键词数据列表
    """
    # 使用默认值
    if priority_keywords is None:
        priority_keywords = []
    
    # 默认类别权重
    if category_weights is None:
        category_weights = {
            "签证类别": 1.2,
            "移民路径": 1.2,
            "政策和机构": 1.3,
            "省份项目": 0.9,
            "实用信息": 0.8,
            "商业移民": 1.0,
            "政治影响": 1.1,
        }
    
    # 获取所有关键词
    all_keywords = []
    for category, keywords in keywords_by_category.items():
        all_keywords.extend(keywords)
    
    # 添加高优先级关键词
    for kw in priority_keywords:
        if kw not in all_keywords:
            all_keywords.append(kw)
    
    # 获取热度分数
    scores = get_keyword_batch_scores(
        all_keywords,
        geo=geo,
        timeframe=timeframe,
        use_serpapi=use_serpapi,
        serpapi_key=serpapi_key
    )
    
    # 计算加权分数
    weighted_scores = {}
    for category, keywords in keywords_by_category.items():
        category_weight = category_weights.get(category, 1.0)
        for keyword in keywords:
            base_score = scores.get(keyword, 0)
            weighted_scores[keyword] = {
                "keyword": keyword,
                "category": category,
                "base_score": base_score,
                "weighted_score": base_score * category_weight,
                "type": "news_article"
            }
    
    # 添加高优先级关键词的加权分数
    for keyword in priority_keywords:
        if keyword in weighted_scores:
            # 高优先级关键词额外加分
            weighted_scores[keyword]["weighted_score"] *= 1.5
        else:
            base_score = scores.get(keyword, 5)  # 默认给5分
            weighted_scores[keyword] = {
                "keyword": keyword,
                "category": "高优先级",
                "base_score": base_score,
                "weighted_score": base_score * 1.5,  # 高优先级加权
                "type": "news_article"
            }
    
    # 按加权分数排序
    sorted_keywords = sorted(
        weighted_scores.values(), 
        key=lambda x: x["weighted_score"], 
        reverse=True
    )
    
    # 从每个类别选择至少一个关键词（如果有的话）
    final_keywords = []
    categories_covered = set()
    
    # 1. 先选择每个类别中分数最高的关键词
    for category in category_weights.keys():
        if len(final_keywords) >= max_keywords:
            break
            
        # 获取该类别中还未选择的最高分关键词
        category_keywords = [
            k for k in sorted_keywords 
            if k["category"] == category and k["keyword"] not in [x["keyword"] for x in final_keywords]
        ]
        
        if category_keywords and category_keywords[0]["base_score"] > 0:
            final_keywords.append(category_keywords[0])
            categories_covered.add(category)
    
    # 2. 然后选择整体分数最高的关键词填满剩余名额
    remaining_spots = max_keywords - len(final_keywords)
    if remaining_spots > 0:
        # 排除已选的关键词
        remaining_keywords = [
            k for k in sorted_keywords 
            if k["keyword"] not in [x["keyword"] for x in final_keywords]
            and k["base_score"] > 0
        ]
        
        # 添加剩余高分关键词
        final_keywords.extend(remaining_keywords[:remaining_spots])
    
    logger.info(f"类别覆盖情况: {categories_covered}")
    logger.info(f"最终选择的关键词数量: {len(final_keywords)}")
    
    return final_keywords 