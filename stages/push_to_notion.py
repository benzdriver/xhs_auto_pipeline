from notion_client import Client
import os
import datetime
from utils.load_config import load_all_config
import json
import sys

config = load_all_config()
notion_api_key = config["notion_api_key"]
notion_database_id = config["notion_database_id"]

def run(data):
    notion = Client(auth=notion_api_key)
    database_id = notion_database_id
    success_count = 0
    error_count = 0

    print(f"\n==== 开始推送 {len(data)} 条内容到 Notion ====")
    
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

            print(f"\n处理第 {idx}/{len(data)} 条内容:")
            print(f"标题: {item.get('title', '')[:30]}...")
            
            response = notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Date": {"title": [{"text": {"content": str(datetime.date.today())}}]},
                    "Title": {"rich_text": [{"text": {"content": item.get("title", "")}}]},
                    "Headline": {"rich_text": [{"text": {"content": item.get("headline", "")}}]},
                    "Content": {"rich_text": [{"text": {"content": item.get("content", "")}}]},
                    "types": {"multi_select": [{"name": t} for t in types]},
                    "Keyword": {"multi_select": [{"name": k} for k in keywords]},
                    "Image": {"url": item.get("imgur_url", "")}
                }
            )
            print(f"✅ 成功创建 Notion 页面: {response.get('url', '')}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 创建第 {idx} 条内容时出错: {str(e)}")
            error_count += 1
            continue

    print(f"\n==== Notion 推送完成 ====")
    print(f"成功: {success_count} 条")
    print(f"失败: {error_count} 条")
    return success_count, error_count

if __name__ == "__main__":
    json_path = "data/image_content.json"
    if not os.path.exists(json_path):
        print(f"❌ 文件 {json_path} 不存在！")
        sys.exit(1)

    with open(json_path, "r") as f:
        try:
            data = json.load(f)
            assert isinstance(data, list), "数据应为列表"
            for i, item in enumerate(data):
                for key in ["title", "headline", "content", "image_keywords", "imgur_url", "types"]:
                    if key not in item:
                        print(f"❌ 第{i}项缺少字段: {key}")
                        sys.exit(1)
        except Exception as e:
            print(f"❌ JSON 解析失败: {e}")
            sys.exit(1)
    print("✅ image_content.json 文件存在且内容合理")
    run(data)