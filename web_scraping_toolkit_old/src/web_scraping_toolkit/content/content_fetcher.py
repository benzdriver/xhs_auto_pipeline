"""
网页内容抓取工具

提供了用于抓取网页文章正文内容的工具，支持：
1. 使用 Playwright 进行动态网页内容提取
2. 使用 requests + BeautifulSoup 作为后备方案
"""

import time
import logging
import requests
from typing import Optional, List
from bs4 import BeautifulSoup

# 配置日志
logger = logging.getLogger("web_scraping_toolkit.content")

def fetch_article_content(
    url: str, 
    min_length: int = 200, 
    selectors: Optional[List[str]] = None
) -> Optional[str]:
    """
    抓取网页文章的正文内容
    
    使用两种方法尝试抓取内容：
    1. 首先使用 Playwright（支持JavaScript渲染和动态内容）
    2. 如果失败，则使用 requests + BeautifulSoup 作为后备
    
    Args:
        url: 要抓取的网页URL
        min_length: 有效内容的最小长度
        selectors: 用于定位正文内容的CSS选择器列表
        
    Returns:
        抓取到的文章正文，如果抓取失败则返回None
    """
    # 默认选择器
    if selectors is None:
        selectors = [
            'div.entry-content', 'article', 'div.article-content', 'div#content', 
            'div.post-content', 'div.main-content', 'main', '.article-body'
        ]

    # 1. 先用 Playwright headless browser，自动跳转
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000)
            time.sleep(2)  # 等待页面渲染和跳转
            for sel in selectors:
                try:
                    node = page.query_selector(sel)
                    if node:
                        text = node.inner_text().strip()
                        if len(text) > min_length:
                            browser.close()
                            return text
                except Exception:
                    continue
            # 兜底：取所有段落拼接
            ps = page.query_selector_all('p')
            text = '\n'.join(p.inner_text().strip() for p in ps if p.inner_text())
            browser.close()
            if len(text) > min_length:
                return text
    except Exception as e:
        logger.warning(f"[playwright] 正文抓取失败: {e}")
    
    # 2. 降级用 requests + BeautifulSoup
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for sel in selectors:
            node = soup.select_one(sel)
            if node and len(node.get_text(strip=True)) > min_length:
                return node.get_text(separator='\n', strip=True)
        paragraphs = soup.find_all('p')
        text = '\n'.join(p.get_text(strip=True) for p in paragraphs)
        if len(text) > min_length:
            return text
    except Exception as e:
        logger.warning(f"[requests] 正文抓取失败: {e}")
    
    return None 