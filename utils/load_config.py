import os
import json
from dotenv import load_dotenv

def load_all_config():
    load_dotenv()  # 加载.env 环境变量

    # 加载 config.json 中的内容
    with open("config.json", "r") as f:
        file_config = json.load(f)

    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY", file_config.get("openai_api_key")),
        "openai_model": file_config.get("openai_model", "gpt-4"),
        "dalle_model": file_config.get("dalle_model", "dall-e-3"),
        "notion_api_key": os.getenv("NOTION_API_KEY", file_config.get("notion_api_key")),
        "notion_database_id": os.getenv("NOTION_DATABASE_ID", file_config.get("notion_database_id")),
        "geo": file_config.get("geo", "CA"),
        "trending_keywords": file_config.get("trending_keywords", []),
        "imgur_client_id": os.getenv("IMGUR_CLIENT_ID", file_config.get("imgur_client_id")),
        "imgur_client_secret": os.getenv("IMGUR_CLIENT_SECRET", file_config.get("imgur_client_secret"))
    }

    return config
