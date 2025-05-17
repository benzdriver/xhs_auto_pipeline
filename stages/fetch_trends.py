from pytrends.request import TrendReq
import math
import requests
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
import hashlib
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import random
import tempfile
import shutil
import pandas as pd  # 明确导入pandas

# 添加 pandas 设置解决 FutureWarning
pd.set_option('future.no_silent_downcasting', True)

# 添加父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added parent directory to PYTHONPATH: {parent_dir}")

from utils.logger import get_logger, log_stage_start, log_stage_end, log_error
# 移除本地代理管理器和验证码解决器的导入
# from utils.proxy_manager import ProxyManager
# from utils.captcha_solver import CaptchaSolver
from utils.load_config import load_all_config

# 引入 web_scraping_toolkit 中的模块
from web_scraping_toolkit.trends import (
    get_trend_score_via_serpapi as wst_get_trend_score_via_serpapi,
    get_trend_score_via_pytrends as wst_get_trend_score_via_pytrends,
    get_keyword_batch_scores as wst_get_keyword_batch_scores,
    use_fallback_score as wst_use_fallback_score,
    fetch_weighted_trending_keywords as wst_fetch_weighted_trending_keywords
)

from web_scraping_toolkit.content import (
    fetch_article_content as wst_fetch_article_content,
    check_cached_news as wst_check_cached_news,
    update_news_cache as wst_update_news_cache,
    mark_news_processed as wst_mark_news_processed,
    is_news_cached as wst_is_news_cached,
    is_news_processed_by_stage as wst_is_news_processed_by_stage,
    get_unprocessed_news as wst_get_unprocessed_news
)

# 使用 web_scraping_toolkit 的 ProxyManager 和 CaptchaSolver
from web_scraping_toolkit import ProxyManager, CaptchaSolver

# 初始化日志
logger = get_logger("fetch_trends")

# 加载配置
config = load_all_config()
trends_config = config.get("trends", {})

# 初始化验证码解决器，使用工具包中的实现
captcha_solver = None
if trends_config.get("use_captcha_solver", False):
    try:
        captcha_solver = CaptchaSolver()
        logger.info("已初始化 web_scraping_toolkit 验证码解决器")
    except Exception as e:
        logger.warning(f"初始化验证码解决器失败: {e}")

# 不再初始化本地代理管理器，改为使用 web_scraping_toolkit 的 ProxyManager
# 默认不使用代理，除非配置中明确指定
use_proxy = trends_config.get("use_proxy", False)
proxy_manager = None
if use_proxy:
    try:
        proxy_manager = ProxyManager()
        logger.info("已初始化 web_scraping_toolkit 代理管理器")
    except Exception as e:
        logger.warning(f"初始化代理管理器失败: {e}")

# 定义各来源的权重
SOURCE_WEIGHTS = {
    "official_announcement": 10.0,  # 官方公告权重最高
    "court_decision": 8.0,          # 法院判决次之
    "political_statement": 6.0,     # 政府动态再次
    "news_article": 4.0,            # 普通新闻权重较低
}

# 定义各类别的权重
CATEGORY_WEIGHTS = {
    "签证类别": 1.2,
    "移民路径": 1.2,
    "政策和机构": 1.3,
    "省份项目": 0.9,
    "实用信息": 0.8,
    "商业移民": 1.0,
    "政治影响": 1.1,
}

# 获取配置的趋势参数
# 移除不需要的代理限制参数
# IP_REQUEST_LIMIT = trends_config.get("max_requests_per_ip", 10)  # 每个IP的请求限制
# IP_COOLDOWN_MINUTES = trends_config.get("ip_cooldown_minutes", 60)  # IP冷却时间（分钟）
DEFAULT_GEO = trends_config.get("default_geo", "CA")  # 默认地区
DEFAULT_TIMEFRAME = trends_config.get("default_timeframe", "now 7-d")  # 默认时间范围

# 简化获取代理的函数
def get_proxy():
    """获取代理IP地址，如果已配置使用代理"""
    if proxy_manager:
        try:
            return proxy_manager.get_playwright_proxy()
        except Exception as e:
            logger.warning(f"获取代理失败: {e}")
    return None

# 移除不需要的代理计数器
# ip_request_counter = {}

def is_valuable_gov_news(title, summary):
    keep_keywords = [
        "policy", "update", "announcement", "news", "change", "regulation", "新政", "公告", "调整"
    ]
    filter_keywords = [
        "form", "application", "apply", "guide", "download", "表格", "申请表", "指南", "下载"
    ]
    text = (title or "") + " " + (summary or "")
    text_lower = text.lower()
    if any(k in text_lower for k in keep_keywords):
        return True
    if any(k in text_lower for k in filter_keywords):
        return False
    return True

def get_trend_score(keyword, pytrends, geo="CA", timeframe="now 7-d"):
    """获取单个关键词的Google Trends热度分数 (使用 PyTrends 库)"""
    # 使用 web_scraping_toolkit 中的函数
    return wst_get_trend_score_via_pytrends(keyword, geo, timeframe)

def get_trend_score_via_browser(keyword, geo="CA", timeframe="now 7-d", bypass_proxy=False):
    """[已弃用] 通过浏览器直接从Google Trends网页抓取热度数据
    
    此方法已弃用，请使用 get_trend_score_via_serpapi 或 get_trend_score_via_pytrends
    """
    logger.warning(f"尝试使用已弃用的浏览器方法获取关键词 '{keyword}' 的趋势分数")
    logger.warning("浏览器方法已弃用，建议使用 SerpAPI 或 PyTrends API")
    return wst_use_fallback_score(keyword)

# 以下提取方法已弃用，保留方法签名以保持兼容性
def extract_method1_datapoints(page, keyword, screenshot_path):
    """[已弃用] 尝试从页面中提取数据点"""
    logger.warning("调用已弃用的提取方法: extract_method1_datapoints")
    return None

def extract_method2_javascript(page, keyword, screenshot_path):
    """[已弃用] 尝试使用JavaScript从页面中提取数据"""
    logger.warning("调用已弃用的提取方法: extract_method2_javascript")
    return None

def extract_method3_selectors(page, keyword, screenshot_path):
    """[已弃用] 尝试使用CSS选择器从页面中提取数据"""
    logger.warning("调用已弃用的提取方法: extract_method3_selectors")
    return None

def extract_method4_svg_elements(page, keyword, screenshot_path):
    """[已弃用] 尝试从SVG元素中提取数据"""
    logger.warning("调用已弃用的提取方法: extract_method4_svg_elements")
    return None

def extract_method5_ocr(page, keyword, screenshot_path):
    """[已弃用] 尝试使用OCR从截图中提取数据"""
    logger.warning("调用已弃用的提取方法: extract_method5_ocr")
    return None

def get_trend_score_via_serpapi(keyword, geo="CA", timeframe="now 7-d"):
    """通过SerpAPI获取Google Trends数据
    
    该函数是 web_scraping_toolkit.trends.get_trend_score_via_serpapi 的封装，
    提供与原有系统的兼容性。
    """
    # 获取 SerpAPI 密钥
    api_key = os.environ.get("SERPAPI_KEY", trends_config.get("serpapi_key"))
    
    # 调用工具包中的实现
    return wst_get_trend_score_via_serpapi(keyword, geo, timeframe, api_key=api_key)

def use_fallback_score(keyword):
    """当所有提取方法都失败时，使用预定义的分数作为后备
    
    该函数是 web_scraping_toolkit.trends.use_fallback_score 的封装，
    提供与原有系统的兼容性。
    """
    # 调用工具包中的实现
    return wst_use_fallback_score(keyword)

def get_keyword_batch_scores(keywords, geo="CA", timeframe="now 7-d"):
    """批量获取关键词的热度分数，优先使用SerpAPI，然后是PyTrends API
    
    该函数是 web_scraping_toolkit.trends.get_keyword_batch_scores 的封装，
    提供与原有系统的兼容性。
    """
    # 配置是否使用 SerpAPI
    use_serpapi = os.environ.get("USE_SERPAPI", "").lower() == "true" or trends_config.get("use_serpapi", False)
    
    # 获取 SerpAPI 密钥
    serpapi_key = os.environ.get("SERPAPI_KEY", trends_config.get("serpapi_key"))
    
    # 调用工具包中的实现
    return wst_get_keyword_batch_scores(
        keywords=keywords,
        geo=geo,
        timeframe=timeframe,
        use_serpapi=use_serpapi,
        serpapi_key=serpapi_key
    )

def fetch_ircc_announcements():
    """抓取IRCC官方公告"""
    try:
        url = "https://www.canada.ca/en/immigration-refugees-citizenship/news/notices.html"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        announcements = []
        articles = soup.select('article')
        
        for article in articles[:5]:  # 只取最新的5条
            title_elem = article.select_one('h2 a')
            if title_elem:
                title = title_elem.text.strip()
                link = "https://www.canada.ca" + title_elem['href'] if title_elem.has_attr('href') else ""
                date_elem = article.select_one('time')
                published_date = date_elem['datetime'] if date_elem and date_elem.has_attr('datetime') else ""
                
                announcements.append({
                    "title": title,
                    "url": link,
                    "type": "official_announcement",
                    "source": "IRCC",
                    "published_date": published_date,
                    "category": "官方公告",
                    "score": SOURCE_WEIGHTS["official_announcement"] * 10
                })
        
        return announcements
    except Exception as e:
        log_error(logger, f"抓取IRCC公告失败: {e}")
        return []

def check_cached_announcements():
    """检查本地缓存的公告，避免重复处理"""
    cache_path = "data/announcement_cache.json"
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def update_cached_announcements(announcements):
    """更新本地缓存的公告"""
    cache_path = "data/announcement_cache.json"
    cached = check_cached_announcements()
    
    # 添加新公告到缓存
    for announcement in announcements:
        announcement_id = hashlib.md5(announcement["url"].encode()).hexdigest()
        if announcement_id not in cached:
            cached[announcement_id] = {
                "title": announcement["title"],
                "url": announcement["url"],
                "first_seen": datetime.now().isoformat(),
                "processed": False
            }
    
    os.makedirs("data", exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cached, f, ensure_ascii=False, indent=2)

def fetch_weighted_trending_keywords(max_keywords=10):
    """获取加权后的热门关键词"""
    # 分类关键词
    keyword_categories = {
        "签证类别": [
            "Canada immigration", "Express Entry", "PR card", "Study permit", "Work permit", 
            "Visitor visa", "Family sponsorship", "Super visa", "PGWP", "Open work permit"
        ],
        "移民路径": [
            "PNP", "Atlantic Immigration", "Rural Immigration", "Startup visa", "Self-employed immigration",
            "Caregiver pathway", "Quebec immigration", "Business immigration", "Skilled worker"
        ],
        "政策和机构": [
            "IRCC", "Immigration Canada", "LMIA", "NOC", "CRS score", "FSW program", "Canadian experience",
            "Immigration policy update", "New immigration program", "Canada citizenship"
        ],
        "省份项目": [
            "Ontario PNP", "BC PNP", "Alberta advantage", "Saskatchewan immigrant", "Manitoba PNP",
            "Nova Scotia immigration", "New Brunswick immigration", "PEI immigration"
        ],
        "实用信息": [
            "Immigration processing time", "Language test", "IELTS", "CELPIP", "ECA", "Medical exam", 
            "Immigration lawyer", "Immigration consultant", "Police certificate"
        ],
        "商业移民": [
            "Canada investor visa", "Entrepreneur immigration", "Start-up visa Canada", 
            "Business experience immigration", "Investor program", "Quebec investor",
            "Self-employed immigration", "Net worth requirement"
        ],
        "政治影响": [
            "Liberal immigration policy", "Conservative immigration", "Immigration minister statement",
            "Immigration debate Canada", "Trudeau immigration", "Canada immigration levels",
            "Election immigration promise", "Political immigration reform"
        ]
    }
    
    # 添加高优先级关键词（无论热度如何，都会考虑）
    priority_keywords = [
        "Express Entry draw", "CRS cutoff", "IRCC announcement", "Canada immigration levels",
        "PR processing time", "Immigration policy change"
    ]
    
    # 配置是否使用 SerpAPI
    use_serpapi = os.environ.get("USE_SERPAPI", "").lower() == "true" or trends_config.get("use_serpapi", False)
    
    # 获取 SerpAPI 密钥
    serpapi_key = os.environ.get("SERPAPI_KEY", trends_config.get("serpapi_key"))
    
    # 调用工具包中的实现
    return wst_fetch_weighted_trending_keywords(
        keywords_by_category=keyword_categories,
        priority_keywords=priority_keywords,
        category_weights=CATEGORY_WEIGHTS,
        max_keywords=max_keywords,
        geo=DEFAULT_GEO,
        timeframe=DEFAULT_TIMEFRAME,
        use_serpapi=use_serpapi,
        serpapi_key=serpapi_key
    )

def fetch_article_content(url, min_length=200):
    """抓取文章内容
    
    该函数是 web_scraping_toolkit.content.fetch_article_content 的封装，
    提供与原有系统的兼容性。
    """
    return wst_fetch_article_content(url, min_length)

def check_cached_news():
    """检查本地缓存的新闻，避免重复处理
    
    该函数是 web_scraping_toolkit.content.check_cached_news 的封装，
    提供与原有系统的兼容性。
    """
    return wst_check_cached_news()

def update_news_cache(news_items):
    """更新本地缓存的新闻
    
    该函数是 web_scraping_toolkit.content.update_news_cache 的封装，
    提供与原有系统的兼容性。
    """
    return wst_update_news_cache(news_items)

def mark_news_processed(url, stage_name):
    """标记新闻已被某个阶段处理
    
    该函数是 web_scraping_toolkit.content.mark_news_processed 的封装，
    提供与原有系统的兼容性。
    """
    return wst_mark_news_processed(url, stage_name)

def is_news_cached(url, cached_news=None):
    """检查新闻是否已被缓存过
    
    该函数是 web_scraping_toolkit.content.is_news_cached 的封装，
    提供与原有系统的兼容性。
    """
    return wst_is_news_cached(url, cached_news)

def is_news_processed_by_stage(url, stage_name, cached_news=None):
    """检查新闻是否已被特定阶段处理过
    
    该函数是 web_scraping_toolkit.content.is_news_processed_by_stage 的封装，
    提供与原有系统的兼容性。
    """
    return wst_is_news_processed_by_stage(url, stage_name, cached_news)

def get_unprocessed_news(stage_name):
    """获取尚未被特定阶段处理的新闻
    
    该函数是 web_scraping_toolkit.content.get_unprocessed_news 的封装，
    提供与原有系统的兼容性。
    """
    return wst_get_unprocessed_news(stage_name)

def fetch_news_items(keyword_data, max_items=5, exclude_sources=None):
    """获取单个关键词的新闻条目"""
    if exclude_sources is None:
        exclude_sources = []
    
    keyword = keyword_data["keyword"]
    category = keyword_data["category"]
    keyword_type = keyword_data.get("type", "news_article")
    base_score = keyword_data.get("base_score", 0)
    
    # 获取缓存的新闻
    cached_news = check_cached_news()
    
    url = f"https://news.google.com/rss/search?q={keyword.replace(' ', '+')}&hl=en-CA&gl=CA&ceid=CA:en"
    try:
        resp = requests.get(url)
        root = ET.fromstring(resp.content)
        items = []
        fetched_count = 0
        
        for item in root.findall('.//item'):
            title = item.find('title').text
            link = item.find('link').text
            source = item.find('source').text if item.find('source') is not None else ""
            summary = item.find('description').text if item.find('description') is not None else None
            
            # 提取发布时间 (pubDate)
            pub_date = None
            if item.find('pubDate') is not None:
                try:
                    pub_date_str = item.find('pubDate').text
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z").isoformat()
                except Exception as e:
                    logger.warning(f"解析发布时间失败: {e}")
            
            # 检查是否已缓存
            if is_news_cached(link, cached_news):
                logger.info(f"跳过已缓存新闻: {title}")
                continue
            
            # 智能过滤官方网站内容
            if source == "canada.ca":
                if not is_valuable_gov_news(title, summary):
                    continue
            
            if source in exclude_sources:
                continue
            
            # 抓取正文
            full_content = fetch_article_content(link)
            if full_content:
                logger.info(f"{title} | 抓取到正文 {len(full_content)} 字")
            else:
                logger.info(f"{title} | 未抓到正文")
            
            # 计算新闻分数
            # 新闻排名越靠前，分数越高
            rank_factor = max(0.5, 1.0 - (fetched_count * 0.1))  # 排名每降低一位，分数降低10%，最低降至50%
            news_score = SOURCE_WEIGHTS.get(keyword_type, 4.0) * base_score * rank_factor
            
            # 生成唯一ID
            news_id = hashlib.md5(link.encode()).hexdigest()[:8]
            
            items.append({
                "id": news_id,
                "title": title,
                "url": link,
                "summary": summary,
                "ranking": fetched_count + 1,
                "source": source,
                "full_content": full_content,
                "keyword": keyword,
                "category": category,
                "score": news_score,
                "type": keyword_type,
                "fetch_date": datetime.now().isoformat(),
                "publish_date": pub_date
            })
            
            fetched_count += 1
            if fetched_count >= max_items:
                break
                
        return items
    except Exception as e:
        log_error(logger, f"获取关键词 '{keyword}' 的新闻失败: {e}")
        return []

def fetch_all_news_data(keyword_data_list, max_items_per_kw=3, max_total_items=15):
    """获取所有关键词的新闻数据"""
    all_news = []
    
    # 先获取官方公告
    official_announcements = fetch_ircc_announcements()
    update_cached_announcements(official_announcements)  # 更新公告缓存
    all_news.extend(official_announcements)
    
    # 获取关键词相关新闻
    for keyword_data in keyword_data_list:
        keyword = keyword_data["keyword"]
        logger.info(f"正在获取关键词 '{keyword}' 的相关新闻...")
        
        news_items = fetch_news_items(keyword_data, max_items=max_items_per_kw)
        for item in news_items:
            logger.info(f"关键词: {keyword} | 分数: {item['score']:.2f} | 标题: {item['title']}")
        
        all_news.extend(news_items)
    
    # 更新新闻缓存
    update_news_cache(all_news)
    
    # 去重：按URL去重
    unique_news = {}
    for item in all_news:
        if item["url"] not in unique_news or item["score"] > unique_news[item["url"]]["score"]:
            unique_news[item["url"]] = item
    
    # 按分数排序
    sorted_news = sorted(unique_news.values(), key=lambda x: x.get("score", 0), reverse=True)
    
    # 限制总数量
    final_news = sorted_news[:max_total_items]
    
    return final_news

def is_valid_news(item):
    """判断新闻是否有效"""
    summary = item.get('summary', '')
    full_content = item.get('full_content', '')
    title = item.get('title', '')
    
    # 官方公告总是有效的
    if item.get('type') == 'official_announcement':
        return True
    
    # 检查内容长度是否足够
    min_content_length = 1500  # 增加最小内容长度要求
    if full_content and isinstance(full_content, str):
        # 检查是否是幻灯片格式
        if "Slide" in full_content[:20] or full_content.strip().startswith("Slide"):
            logger.warning(f"疑似幻灯片格式，内容可能不完整: {title}")
            # 如果是幻灯片格式，要求更长的内容才视为有效
            if len(full_content.strip()) < min_content_length * 2:
                logger.warning(f"幻灯片内容太短: {len(full_content.strip())} 字符")
                return False
        
        # 正常内容长度检查
        if len(full_content.strip()) > min_content_length:
            return True
        else:
            logger.warning(f"内容长度不足: {len(full_content.strip())} 字符 (要求 {min_content_length}+)")
    
    # 如果没有full_content，则检查summary
    if summary and isinstance(summary, str) and len(summary.strip()) > 100 and '<a href=' not in summary:
        return True
    
    # 过滤不需要的内容
    filter_keywords = ['点击申请', '下载表格', 'application form', 'apply now', 'download', 
                     '表格', '申请表', 'guide', '指南', 'slide']
    
    for kw in filter_keywords:
        if ((summary and kw.lower() in summary.lower()) or 
            (full_content and isinstance(full_content, str) and kw.lower() in full_content.lower())):
            logger.warning(f"发现过滤关键词 '{kw}': {title}")
            return False
    
    return False

def run():
    """运行完整流程"""
    log_stage_start(logger, "抓取趋势和新闻")
    start_time = time.time()
    
    try:
        logger.info("==== [阶段1-1] 获取加权热门关键词 ====")
        keyword_data_list = fetch_weighted_trending_keywords(max_keywords=8)
        
        logger.info("\n==== [阶段1-2] 抓取新闻内容 ====")
        news_data = fetch_all_news_data(keyword_data_list, max_items_per_kw=3, max_total_items=15)
        
        logger.info("\n==== [阶段1-3] 过滤有效新闻 ====")
        valid_news = []
        for news in news_data:
            if is_valid_news(news):
                valid_news.append(news)
                logger.info(f"[有效] {news.get('title', '')}")
            else:
                logger.info(f"[无效] {news.get('title', '')}")
        
        # 再次按分数排序
        sorted_valid_news = sorted(valid_news, key=lambda x: x.get("score", 0), reverse=True)
        
        # 保存结果
        os.makedirs("data", exist_ok=True)
        with open("data/news_content.json", "w") as f:
            json.dump(sorted_valid_news, f, ensure_ascii=False, indent=2)
        
        # 标记所有有效新闻为已经被fetch_trends阶段处理
        for news in sorted_valid_news:
            mark_news_processed(news["url"], "fetch_trends")
        
        logger.info(f"共保留 {len(sorted_valid_news)} 条有效新闻，已保存到 data/news_content.json")
        
        log_stage_end(logger, "抓取趋势和新闻", success=True, duration=time.time() - start_time)
        return sorted_valid_news
    except Exception as e:
        log_error(logger, f"抓取趋势和新闻失败: {e}")
        log_stage_end(logger, "抓取趋势和新闻", success=False, duration=time.time() - start_time)
        return []

if __name__ == "__main__":
    run()
