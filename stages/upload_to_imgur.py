import json
import requests
import time
import os
from utils.load_config import load_all_config
from utils.logger import get_logger

# 初始化日志记录器
logger = get_logger("imgur_upload")

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 10  # 秒

def upload_to_imgur(image_path, client_id):
    """将图片上传到Imgur并返回URL，添加重试逻辑"""
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {client_id}"}
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"正在上传图片到Imgur: {os.path.basename(image_path)}...{'(重试 #' + str(attempt+1) + ')' if attempt > 0 else ''}")
            with open(image_path, "rb") as f:
                files = {"image": f}
                response = requests.post(url, headers=headers, files=files, timeout=30)
            
            if response.status_code == 200:
                imgur_url = response.json()["data"]["link"]
                logger.info(f"✅ 图片上传成功: {imgur_url}")
                return imgur_url
            elif response.status_code == 429:  # 速率限制
                retry_after = int(response.headers.get('Retry-After', RETRY_DELAY * 2))
                logger.warning(f"⚠️ 达到Imgur速率限制，等待 {retry_after} 秒后重试...")
                time.sleep(retry_after)
            else:
                logger.error(f"❌ 图片上传失败: {response.status_code} - {response.text}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
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

def run():
    """批量上传图片到Imgur"""
    # 加载配置
    config = load_all_config()
    client_id = config["imgur_client_id"]
    
    if not client_id:
        logger.error("❌ 未配置Imgur Client ID，请在.env文件中设置IMGUR_CLIENT_ID")
        return False

    # 检查输入文件
    input_path = "data/image_content.json"
    if not os.path.exists(input_path):
        logger.error(f"❌ 输入文件 {input_path} 不存在！")
        return False
    
    # 读取图片内容数据
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"❌ 读取内容数据失败: {e}", exc_info=True)
        return False
    
    logger.info(f"读取到 {len(data)} 条内容，开始上传图片...")
    
    # 统计
    success_count = 0
    failed_count = 0
    skipped_count = 0

    # 处理每个内容项
    for i, item in enumerate(data):
        local_path = item.get("final_image_path")
        
        # 如果已经有Imgur URL或没有本地图片路径，则跳过
        if item.get("imgur_url") or not local_path:
            logger.info(f"⏩ 跳过第 {i+1}/{len(data)} 条内容: 已有Imgur URL或无本地图片")
            skipped_count += 1
            continue
        
        # 检查本地图片是否存在
        if not os.path.exists(local_path):
            logger.warning(f"⚠️ 第 {i+1}/{len(data)} 条内容的本地图片不存在: {local_path}")
            failed_count += 1
            continue
        
        logger.info(f"\n处理第 {i+1}/{len(data)} 条内容:")
        
        # 上传图片
        imgur_url = upload_to_imgur(local_path, client_id)
        if imgur_url:
            item["imgur_url"] = imgur_url
            success_count += 1
            logger.info(f"✅ 成功上传图片: {os.path.basename(local_path)} -> {imgur_url}")
        else:
            failed_count += 1
            logger.error(f"❌ 上传失败: {os.path.basename(local_path)}")
        
        # 添加延迟，避免API限制
        if i < len(data) - 1:
            delay = 5
            logger.info(f"等待{delay}秒后处理下一条内容...")
            time.sleep(delay)
    
    # 保存更新后的数据
    try:
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✅ 已更新 {input_path}")
    except Exception as e:
        logger.error(f"❌ 保存数据失败: {e}", exc_info=True)
        return False
    
    # 打印统计信息
    logger.info(f"\n图片上传完成:")
    logger.info(f"- 成功: {success_count} 张")
    logger.info(f"- 失败: {failed_count} 张")
    logger.info(f"- 跳过: {skipped_count} 张")
    
    return success_count > 0

if __name__ == "__main__":
    run()
