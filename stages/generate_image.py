import os
import sys
import json
import base64
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.load_config import load_all_config
from utils.cache_utils import mark_news_processed, is_news_processed_by_stage
from utils.logger import get_logger, log_stage_start, log_stage_end, log_error

# 初始化日志记录器
logger = get_logger("generate_image")

# 加载配置
config = load_all_config()
OPENAI_API_KEY = config["openai_api_key"]
DALLE_MODEL = config.get("dalle_model", "dall-e-3")
IMGUR_CLIENT_ID = config["imgur_client_id"]
IMGUR_CLIENT_SECRET = config.get("imgur_client_secret", "")

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒

def generate_image_prompt(title: str, headline: str, keywords: List[str]) -> tuple:
    """生成适合DALL-E的图像提示，返回中英文提示词
    
    Returns:
        tuple: (中文提示词, 英文提示词)
    """
    # 构建中文基本提示
    base_prompt_zh = f"为小红书平台创建一张关于加拿大移民的精美图片，主题是：{title}。"
    
    # 添加关键词
    if keywords:
        keywords_str = "，".join(keywords[:3])  # 最多使用3个关键词
        base_prompt_zh += f" 图片应包含以下元素：{keywords_str}。"
    
    # 提取内容中的重要场景或元素
    scene_elements = []
    # 如果标题中包含"快速通道"或"Express Entry"，添加相关元素
    if any(term in title for term in ["快速通道", "快速入境", "Express Entry"]):
        scene_elements.append("加拿大移民局办公场景")
        scene_elements.append("电子申请系统界面")
    
    # 如果标题中包含"PNP"或"省提名"，添加相关元素
    if any(term in title for term in ["PNP", "省提名"]):
        scene_elements.append("加拿大省份地图")
        scene_elements.append("省政府建筑")
    
    # 如果标题中包含特定职业，添加相关元素
    if "牙医" in title or "dentist" in title.lower():
        scene_elements.append("现代牙医诊所")
        scene_elements.append("专业医疗环境")
    
    if scene_elements:
        base_prompt_zh += f" 建议场景：{', '.join(scene_elements)}。"
    
    # 添加中文风格指导
    style_guide_zh = """风格要求：
    1. 使用明亮、温暖的色调
    2. 包含加拿大元素（如枫叶、国旗或地标）
    3. 画面清晰、美观，适合社交媒体分享
    4. 风格现代、时尚，符合小红书平台审美
    5. 不要包含任何文字或标题"""
    
    final_prompt_zh = f"{base_prompt_zh} {style_guide_zh}"
    
    # 构建详细的英文提示词，针对Diffusion模型优化
    # 提取标题的主题
    main_subject = title
    
    # 提取标题中的关键信息
    headline_extract = headline[:50] if headline else ""
    
    # 确定图片的主要场景
    main_scene = "modern Canadian cityscape"
    if any(term in title.lower() for term in ["快速通道", "express entry", "快速入境"]):
        main_scene = "Canadian immigration office with digital application system"
    elif any(term in title.lower() for term in ["pnp", "省提名"]):
        main_scene = "provincial government building with Canadian and provincial flags"
    elif any(term in title.lower() for term in ["牙医", "dentist", "医生", "doctor"]):
        main_scene = "modern Canadian dental clinic or healthcare facility"
    
    cover_prompt_eng = f"""Create a professional, eye-catching image for Xiaohongshu (RED Note) platform about Canadian immigration.

MAIN SUBJECT: {main_subject}

MAIN SCENE: {main_scene}

CONTEXT: {headline_extract}

KEY ELEMENTS TO INCLUDE:
- {', '.join(keywords[:3])}
{('- ' + '\n- '.join(scene_elements)) if scene_elements else ''}
- Canadian symbols (maple leaf, flag)
- Professional, optimistic atmosphere

STYLE SPECIFICATIONS:
- Photorealistic, high-definition photography style
- Bright, warm color palette 
- Clean composition with clear focal point
- Modern, aspirational lifestyle aesthetic
- Suitable for social media sharing

TECHNICAL DETAILS:
- Ultra high resolution, 4K quality
- Sharp focus on main elements
- No text or watermarks

MOOD: Inspiring, hopeful, welcoming, professional"""
    
    return final_prompt_zh, cover_prompt_eng

def generate_dalle_image(prompt: str) -> Optional[str]:
    """使用DALL-E生成图像并返回URL，添加重试逻辑"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": DALLE_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "standard",
        "response_format": "url"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"正在生成图片，提示：{prompt[:50]}...{'(重试 #' + str(attempt+1) + ')' if attempt > 0 else ''}")
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60  # 增加超时时间
            )
            
            if response.status_code == 200:
                result = response.json()
                image_url = result["data"][0]["url"]
                logger.info(f"✅ 图片生成成功")
                return image_url
            elif response.status_code == 429:  # 速率限制
                retry_after = int(response.headers.get('Retry-After', RETRY_DELAY))
                logger.warning(f"⚠️ 达到API速率限制，等待 {retry_after} 秒后重试...")
                time.sleep(retry_after)
            elif response.status_code >= 500:  # 服务器错误
                logger.warning(f"⚠️ OpenAI服务器错误 ({response.status_code})，等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"❌ 图片生成失败: {response.status_code} - {response.text}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                else:
                    return None
        except Exception as e:
            logger.error(f"❌ 图片生成异常: {e}", exc_info=True)
            if attempt < MAX_RETRIES - 1:
                logger.info(f"等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                return None
    
    return None

def upload_to_imgur(image_url: str) -> Optional[str]:
    """将图片上传到Imgur并返回URL，添加重试逻辑"""
    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }
    
    data = {
        "image": image_url,
        "type": "url",
        "title": "加拿大移民信息图片",
        "description": "由AI生成的加拿大移民信息图片"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"正在上传图片到Imgur...{'(重试 #' + str(attempt+1) + ')' if attempt > 0 else ''}")
            response = requests.post(
                "https://api.imgur.com/3/image",
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                imgur_url = result["data"]["link"]
                logger.info(f"✅ 图片上传成功: {imgur_url}")
                return imgur_url
            elif response.status_code == 429:  # 速率限制
                retry_after = int(response.headers.get('Retry-After', RETRY_DELAY * 2))
                logger.warning(f"⚠️ 达到Imgur速率限制，等待 {retry_after} 秒后重试...")
                time.sleep(retry_after)
            else:
                logger.error(f"❌ 图片上传失败: {response.status_code} - {response.text}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"等待 {RETRY_DELAY * 2} 秒后重试...")
                    time.sleep(RETRY_DELAY * 2)  # Imgur的速率限制通常需要更长的等待时间
                else:
                    return None
        except Exception as e:
            logger.error(f"❌ 图片上传异常: {e}", exc_info=True)
            if attempt < MAX_RETRIES - 1:
                logger.info(f"等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                return None
    
    return None

def process_content_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """处理单个内容项并生成图片"""
    title = item.get("title", "")
    headline = item.get("headline", "")
    
    # 获取或创建图片关键词
    if "image_keywords" not in item or not item["image_keywords"]:
        # 如果没有图片关键词，从标题和内容中提取
        keywords = [k.strip() for k in title.split(" ") if len(k.strip()) > 1]
        if len(keywords) < 3 and "content" in item:
            # 从内容中提取更多关键词
            content_words = [w for w in item["content"][:100].split(" ") if len(w) > 3]
            keywords.extend(content_words[:3])
        
        item["image_keywords"] = keywords[:5]  # 最多使用5个关键词
    
    # 检查是否已有提示词，如果有则优化，如果没有则生成
    if "cover_prompt" in item and "cover_prompt_eng" in item:
        logger.info(f"使用并优化现有提示词")
        cover_prompt_zh = item["cover_prompt"]
        cover_prompt_eng = item["cover_prompt_eng"]
        
        # 检查英文提示词是否已经是详细格式
        if "MAIN SUBJECT:" not in cover_prompt_eng:
            # 如果不是详细格式，则替换为详细格式
            
            # 提取内容中的重要场景或元素
            scene_elements = []
            # 如果标题中包含"快速通道"或"Express Entry"，添加相关元素
            if any(term in title for term in ["快速通道", "快速入境", "Express Entry"]):
                scene_elements.append("加拿大移民局办公场景")
                scene_elements.append("电子申请系统界面")
            
            # 如果标题中包含"PNP"或"省提名"，添加相关元素
            if any(term in title for term in ["PNP", "省提名"]):
                scene_elements.append("加拿大省份地图")
                scene_elements.append("省政府建筑")
            
            # 如果标题中包含特定职业，添加相关元素
            if "牙医" in title or "dentist" in title.lower():
                scene_elements.append("现代牙医诊所")
                scene_elements.append("专业医疗环境")
                
            # 确定图片的主要场景
            main_scene = "modern Canadian cityscape"
            if any(term in title.lower() for term in ["快速通道", "express entry", "快速入境"]):
                main_scene = "Canadian immigration office with digital application system"
            elif any(term in title.lower() for term in ["pnp", "省提名"]):
                main_scene = "provincial government building with Canadian and provincial flags"
            elif any(term in title.lower() for term in ["牙医", "dentist", "医生", "doctor"]):
                main_scene = "modern Canadian dental clinic or healthcare facility"
            
            headline_extract = headline[:50] if headline else ""
            
            cover_prompt_eng = f"""Create a professional, eye-catching image for Xiaohongshu (RED Note) platform about Canadian immigration.

MAIN SUBJECT: {title}

MAIN SCENE: {main_scene}

CONTEXT: {headline_extract}

KEY ELEMENTS TO INCLUDE:
- {', '.join(item.get("image_keywords", ["加拿大", "移民"])[:3])}
{('- ' + '\n- '.join(scene_elements)) if scene_elements else ''}
- Canadian symbols (maple leaf, flag)
- Professional, optimistic atmosphere

STYLE SPECIFICATIONS:
- Photorealistic, high-definition photography style
- Bright, warm color palette 
- Clean composition with clear focal point
- Modern, aspirational lifestyle aesthetic
- Suitable for social media sharing

TECHNICAL DETAILS:
- Ultra high resolution, 4K quality
- Sharp focus on main elements
- No text or watermarks

MOOD: Inspiring, hopeful, welcoming, professional"""
        
        # 检查中文提示词是否包含风格指导
        if "风格要求" not in cover_prompt_zh:
            # 添加风格指导
            style_guide_zh = """风格要求：
    1. 使用明亮、温暖的色调
    2. 包含加拿大元素（如枫叶、国旗或地标）
    3. 画面清晰、美观，适合社交媒体分享
    4. 风格现代、时尚，符合小红书平台审美
    5. 不要包含任何文字或标题"""
            cover_prompt_zh = f"{cover_prompt_zh} {style_guide_zh}"
        
        # 更新提示词
        item["cover_prompt"] = cover_prompt_zh
        item["cover_prompt_eng"] = cover_prompt_eng
    else:
        # 生成图片提示（中英文）
        cover_prompt_zh, cover_prompt_eng = generate_image_prompt(
            title=title,
            headline=headline,
            keywords=item.get("image_keywords", [])
        )
        
        # 保存提示词到内容项
        item["cover_prompt"] = cover_prompt_zh
        item["cover_prompt_eng"] = cover_prompt_eng
    
    # 生成图片
    image_url = generate_dalle_image(item["cover_prompt_eng"])  # 使用英文提示词生成图片
    if not image_url:
        logger.warning(f"⚠️ 无法为内容 '{title}' 生成图片")
        return item
    
    # 上传到Imgur
    imgur_url = upload_to_imgur(image_url)
    if imgur_url:
        item["imgur_url"] = imgur_url
        item["original_image_url"] = image_url
        logger.info(f"✅ 为内容 '{title}' 添加了图片: {imgur_url}")
    else:
        logger.warning(f"⚠️ 无法为内容 '{title}' 上传图片到Imgur")
        # 即使Imgur上传失败，也保留原始图片URL
        item["original_image_url"] = image_url
    
    return item

def run() -> List[Dict[str, Any]]:
    """运行图片生成流程"""
    log_stage_start(logger, "图片生成")
    start_time = time.time()
    
    # 检查输入文件是否存在
    input_path = "data/generated_langchain_content.json"
    if not os.path.exists(input_path):
        logger.error(f"❌ 输入文件 {input_path} 不存在！")
        log_stage_end(logger, "图片生成", success=False, duration=time.time() - start_time)
        return []
    
    # 读取生成的内容
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content_data = json.load(f)
    except Exception as e:
        log_error(logger, f"❌ 读取内容数据失败: {e}")
        log_stage_end(logger, "图片生成", success=False, duration=time.time() - start_time)
        return []
    
    logger.info(f"读取到 {len(content_data)} 条内容，开始生成图片...")
    
    # 统计
    success_count = 0
    skip_count = 0
    error_count = 0
    
    # 处理每个内容项
    processed_items = []
    for i, item in enumerate(content_data):
        logger.info(f"\n处理第 {i+1}/{len(content_data)} 条内容:")
        
        # 检查是否已处理过
        if "url" in item and is_news_processed_by_stage(item["url"], "generate_image"):
            logger.info(f"⏩ 跳过已处理的内容: {item.get('title', '')}")
            processed_items.append(item)
            skip_count += 1
            continue
        
        # 处理内容项
        try:
            processed_item = process_content_item(item)
            processed_items.append(processed_item)
            
            # 判断处理是否成功（有图片URL）
            if processed_item.get("original_image_url"):
                success_count += 1
            else:
                error_count += 1
            
            # 标记为已处理
            if "url" in item:
                mark_news_processed(item["url"], "generate_image")
        except Exception as e:
            log_error(logger, f"处理内容项时出错: {e}")
            processed_items.append(item)  # 添加原始项，确保不丢失数据
            error_count += 1
        
        # 添加延迟，避免API限制
        if i < len(content_data) - 1:
            delay = RETRY_DELAY
            logger.info(f"等待{delay}秒后处理下一条内容...")
            time.sleep(delay)
    
    # 保存结果到原始文件
    output_path = input_path  # 使用相同的文件路径
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(processed_items, ensure_ascii=False, indent=2, fp=f)
        logger.info(f"\n✅ 图片生成完成，结果已更新到 {output_path}")
    except Exception as e:
        log_error(logger, f"保存结果失败: {e}")
    
    # 输出统计信息
    logger.info(f"\n图片生成统计:")
    logger.info(f"- 总共内容: {len(content_data)} 条")
    logger.info(f"- 成功生成: {success_count} 条")
    logger.info(f"- 已跳过: {skip_count} 条")
    logger.info(f"- 处理失败: {error_count} 条")
    
    # 记录阶段结束
    log_stage_end(logger, "图片生成", success=error_count == 0, duration=time.time() - start_time)
    
    return processed_items

if __name__ == "__main__":
    run()