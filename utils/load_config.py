import os
from dotenv import load_dotenv
import json

def load_all_config():
    """
    加载配置，仅从.env环境变量文件获取
    不再使用config.json
    """
    # 加载.env环境变量
    load_dotenv()  

    # 直接从环境变量获取所有配置
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4"),
        "dalle_model": os.getenv("DALLE_MODEL", "dall-e-3"),
        "notion_api_key": os.getenv("NOTION_API_KEY", ""),
        "notion_database_id": os.getenv("NOTION_DATABASE_ID", ""),
        "geo": os.getenv("GEO", "CA"),
        "trending_keywords": os.getenv("TRENDING_KEYWORDS", "").split(",") if os.getenv("TRENDING_KEYWORDS") else [],
        "imgur_client_id": os.getenv("IMGUR_CLIENT_ID", ""),
        "imgur_client_secret": os.getenv("IMGUR_CLIENT_SECRET", ""),
        
        # 代理配置
        "proxy": {
            "enabled": os.getenv("USE_PROXY", "").lower() == "true",
            "rotation_interval": int(os.getenv("PROXY_ROTATION_INTERVAL", "300")),
            "smartproxy": {
                "username": os.getenv("SMARTPROXY_USERNAME", ""),
                "password": os.getenv("SMARTPROXY_PASSWORD", ""),
                "endpoint": os.getenv("SMARTPROXY_ENDPOINT", "gate.smartproxy.com"),
                "port": os.getenv("SMARTPROXY_PORT", "7000"),
                "additional_ports": os.getenv("SMARTPROXY_ADDITIONAL_PORTS", "").split(",") if os.getenv("SMARTPROXY_ADDITIONAL_PORTS") else []
            },
            "custom_proxies": _parse_custom_proxies()
        },
        
        # 验证码服务配置
        "captcha": {
            "service": os.getenv("CAPTCHA_SERVICE", "2captcha"),
            "api_key": os.getenv("TWOCAPTCHA_API_KEY", "")
        },
        
        # 趋势配置
        "trends": {
            "max_requests_per_ip": int(os.getenv("MAX_REQUESTS_PER_IP", "10")),
            "ip_cooldown_minutes": int(os.getenv("IP_COOLDOWN_MINUTES", "60")),
            "default_geo": os.getenv("GEO", "CA"),
            "default_timeframe": os.getenv("TIMEFRAME", "now 7-d")
        }
    }

    return config

def _parse_custom_proxies():
    """解析自定义代理配置"""
    custom_proxies_json = os.getenv("CUSTOM_PROXIES", "")
    if not custom_proxies_json:
        return []
        
    try:
        return json.loads(custom_proxies_json)
    except json.JSONDecodeError:
        print("警告: 自定义代理配置格式无效，应为有效的JSON数组")
        return []
