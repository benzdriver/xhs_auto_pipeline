import sys
import os

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_client import Client
import datetime
from utils.load_config import load_all_config
import json
from utils.logger import get_logger

# 初始化日志记录器
logger = get_logger("push_to_notion")

config = load_all_config()
notion_api_key = config["notion_api_key"]
notion_database_id = config["notion_database_id"]

def run(data):
    notion = Client(auth=notion_api_key)
    database_id = notion_database_id
    success_count = 0
    error_count = 0

    logger.info(f"\n==== 开始推送 {len(data)} 条内容到 Notion ====")
    
    for idx, item in enumerate(data, 1):
        try:
            # 确保 types 是列表
            types = item.get("types", [])
            if isinstance(types, str):
                types = [types]
            
            # 确保 image_keywords 是列表
            keywords = item.get("image_keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]

            logger.info(f"\n处理第 {idx}/{len(data)} 条内容:")
            logger.info(f"标题: {item.get('title', '')[:30]}...")
            
            # 准备属性字典
            properties = {
                "Date": {"title": [{"text": {"content": str(datetime.date.today())}}]},
                "Title": {"rich_text": [{"text": {"content": item.get("title", "")}}]},
                "Headline": {"rich_text": [{"text": {"content": item.get("headline", "")}}]},
                "Content": {"rich_text": [{"text": {"content": item.get("content", "")}}]},
                "types": {"multi_select": [{"name": t} for t in types]},
                "Keyword": {"multi_select": [{"name": k} for k in keywords[:10]]}  # 限制关键词数量
            }
            
            # 添加CoverPrompt和CoverPromptEng字段（如果存在）
            if item.get("cover_prompt"):
                properties["CoverPrompt"] = {"rich_text": [{"text": {"content": item.get("cover_prompt", "")}}]}
            
            if item.get("cover_prompt_eng"):
                properties["CoverPromptEng"] = {"rich_text": [{"text": {"content": item.get("cover_prompt_eng", "")}}]}
            
            # 只有当imgur_url存在且不为空时才添加Image属性
            if item.get("imgur_url"):
                properties["Image"] = {"url": item.get("imgur_url")}
            
            response = notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            logger.info(f"✅ 成功创建 Notion 页面: {response.get('url', '')}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ 创建第 {idx} 条内容时出错: {str(e)}")
            error_count += 1
            continue

    logger.info(f"\n==== Notion 推送完成 ====")
    logger.info(f"成功: {success_count} 条")
    logger.info(f"失败: {error_count} 条")
    return success_count, error_count

if __name__ == "__main__":
    # 读取内容文件
    json_path = "data/generated_langchain_content.json"
    if not os.path.exists(json_path):
        logger.error(f"❌ 文件 {json_path} 不存在！")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            assert isinstance(data, list), "数据应为列表"
            # 准备内容数据以适配Notion推送格式
            for item in data:
                # 如果没有types字段，添加一个默认值
                if "types" not in item:
                    item["types"] = ["移民资讯"]
                
                # 确保有image_keywords字段，即使为空
                if "image_keywords" not in item:
                    item["image_keywords"] = []
                
                # 检查必要字段
                missing_fields = []
                for key in ["title", "headline", "content"]:
                    if key not in item:
                        missing_fields.append(key)
                
                if missing_fields:
                    logger.warning(f"⚠️ 内容缺少必要字段: {', '.join(missing_fields)}")
        except Exception as e:
            logger.error(f"❌ JSON 解析失败: {e}")
            sys.exit(1)
    logger.info(f"✅ {json_path} 文件存在且内容合理")
    run(data)