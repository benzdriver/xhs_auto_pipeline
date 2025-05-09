from pytrends.request import TrendReq
import math
import requests
import xml.etree.ElementTree as ET
import json
import os
import time
from bs4 import BeautifulSoup

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

def fetch_google_trends_hotwords(geo="CA", timeframe="now 7-d", top_n=5):
    pytrends = TrendReq(hl='en-CA', tz=360)
    kw_list = [
        "Canada immigration", "Express Entry", "PR card", "PNP", "Study permit",
        "Canada visa", "Canada work permit", "Canada citizenship", "IRCC", "Immigration Canada",
        "LMIA"
    ]
    batch_size = 5
    scores = {}
    for i in range(0, len(kw_list), batch_size):
        batch = kw_list[i:i+batch_size]
        try:
            pytrends.build_payload(batch, timeframe=timeframe, geo=geo)
            data = pytrends.interest_over_time()
            if not data.empty:
                for kw in batch:
                    if kw in data:
                        scores[kw] = int(data[kw].mean())
        except Exception as e:
            print(f"[GoogleTrends] 查询 {batch} 失败: {e}")
    if not scores:
        print("[GoogleTrends] 没有获取到任何热度数据！")
        return []
    sorted_keywords = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("[GoogleTrends] 关键词热度排行：", sorted_keywords)
    final_keywords = [kw for kw, score in sorted_keywords if score > 0][:top_n]
    print(f"[ALL] 最终热搜主题: {final_keywords}")
    return final_keywords

def fetch_article_content(url, min_length=200):
    selectors = [
        'div.entry-content', 'article', 'div.article-content', 'div#content', 'div.post-content', 'div.main-content'
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
        print(f"[正文抓取][playwright] 失败: {e}")
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
        print(f"[正文抓取][requests] 失败: {e}")
    return None

def fetch_news_items(keyword, max_items=5, exclude_sources=None):
    if exclude_sources is None:
        exclude_sources = []
    url = f"https://news.google.com/rss/search?q={keyword.replace(' ', '+')}&hl=en-CA&gl=CA&ceid=CA:en"
    resp = requests.get(url)
    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall('.//item'):
        title = item.find('title').text
        link = item.find('link').text
        source = item.find('source').text if item.find('source') is not None else ""
        summary = item.find('description').text if item.find('description') is not None else None
        # 智能过滤官网内容
        if source == "canada.ca":
            if not is_valuable_gov_news(title, summary):
                continue
        if source in exclude_sources:
            continue
        # 新增：自动抓正文
        full_content = fetch_article_content(link)
        if full_content:
            print(f"[正文抓取] {title} | 抓取到正文 {len(full_content)} 字")
        else:
            print(f"[正文抓取] {title} | 未抓到正文")
        items.append({
            "title": title,
            "url": link,
            "summary": summary,
            "ranking": len(items) + 1,
            "source": source,
            "full_content": full_content
        })
        if len(items) >= max_items:
            break
    return items

def fetch_all_news_data(kw_list, max_items_per_kw=5):
    all_news = []
    for kw in kw_list:
        news_items = fetch_news_items(kw, max_items=max_items_per_kw)
        for item in news_items:
            print(f"[NEWS] ranking: {item['ranking']} | title: {item['title']}\nurl: {item['url']}\nsource: {item['source']}\nsummary: {item['summary']}\n---")
        all_news.extend(news_items)
    return all_news

def is_valid_news(summary, full_content):
    # 过滤只有链接、表格、广告、极短内容
    if full_content and isinstance(full_content, str) and len(full_content.strip()) > 200:
        return True
    if summary and isinstance(summary, str) and len(summary.strip()) > 30 and '<a href=' not in summary:
        return True
    for kw in ['点击申请', '下载表格', 'application form', 'apply now', 'download', '表格', '申请表', 'guide', '指南']:
        if (summary and kw in summary) or (full_content and isinstance(full_content, str) and kw in full_content):
            return False
    return False

def run():
    kw_list = fetch_google_trends_hotwords(top_n=5)
    news_data = fetch_all_news_data(kw_list, max_items_per_kw=5)
    valid_news = []
    for news in news_data:
        summary = news.get('summary', '')
        full_content = news.get('full_content', '')
        if is_valid_news(summary, full_content):
            valid_news.append(news)
        else:
            print(f"[WARN] 跳过无效新闻: {news.get('title', '')}")
    os.makedirs("data", exist_ok=True)
    with open("data/news_content.json", "w") as f:
        json.dump(valid_news, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 共保留 {len(valid_news)} 条有效新闻，已保存到 data/news_content.json")
    return valid_news

if __name__ == "__main__":
    run()
