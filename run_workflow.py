#!/usr/bin/env python
"""
自动化小红书内容生成工作流
整合了所有步骤，从抓取趋势到生成内容并推送到Notion
"""

import os
import json
import subprocess
import time
from datetime import datetime
import sys
from dotenv import load_dotenv
from utils.logger import get_workflow_logger, log_stage_start, log_stage_end, log_error

# 初始化主工作流日志记录器
logger = get_workflow_logger()

# 加载环境变量
load_dotenv()

# 导入模块
try:
    from stages.push_to_notion import run as push_to_notion
except ImportError as e:
    module_name = str(e).split("'")[-2] if "'" in str(e) else str(e)
    logger.warning(f"无法导入push_to_notion模块: {e}")
    logger.info(f"提示: 确保 {module_name} 模块存在并且可以被正确导入")
    push_to_notion = None

try:
    from stages.upload_to_imgur import run as upload_to_imgur
except ImportError as e:
    module_name = str(e).split("'")[-2] if "'" in str(e) else str(e)
    logger.warning(f"无法导入upload_to_imgur模块: {e}")
    logger.info(f"提示: 确保 {module_name} 模块存在并且可以被正确导入")
    upload_to_imgur = None

def run_command(command, description):
    """运行命令并输出结果"""
    log_stage_start(logger, description)
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True,
            text=True,
            capture_output=True
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(f"警告: {result.stderr}")
        
        duration = time.time() - start_time
        log_stage_end(logger, description, success=True, duration=duration)
        return True
    except subprocess.CalledProcessError as e:
        # 提取错误信息并尝试提供有用的建议
        error_output = e.stderr
        log_error(logger, f"{description}失败: {e}")
        logger.error(f"错误输出: {error_output}")
        
        # 检查常见错误类型并提供更有用的错误消息
        if "ModuleNotFoundError: No module named" in error_output:
            module_name = error_output.split("No module named")[-1].strip().replace("'", "").strip()
            logger.error(f"缺少必要的模块: {module_name}")
            logger.info(f"解决方案: 请确保 {module_name} 模块存在。如果是自定义模块，创建相应的目录和文件；如果是第三方库，使用 pip install {module_name} 安装。")
        elif "ImportError:" in error_output:
            logger.error("导入错误: 无法导入所需模块")
            logger.info("解决方案: 检查项目结构和导入路径")
        elif "SyntaxError:" in error_output:
            logger.error("语法错误: 代码中存在语法问题")
            logger.info("解决方案: 检查错误行附近的代码，修复语法问题")
        
        log_stage_end(logger, description, success=False, duration=time.time() - start_time)
        return False

def log_workflow_results(workflow_name, results):
    """记录工作流程执行结果"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📝 工作流程日志已保存到: {log_file}")

def prepare_content_for_notion(content_data):
    """准备内容数据以适配Notion推送格式"""
    for item in content_data:
        # 如果没有types字段，添加一个默认值
        if "types" not in item:
            item["types"] = ["移民资讯"]
        
        # 确保有imgur_url字段，即使为空
        if "imgur_url" not in item:
            item["imgur_url"] = ""
    
    return content_data

def check_notion_config():
    """检查Notion环境变量配置是否有效"""
    notion_api_key = os.getenv("NOTION_API_KEY", "")
    notion_database_id = os.getenv("NOTION_DATABASE_ID", "")
    
    # 检查是否为空
    if not notion_api_key or not notion_database_id:
        return False, "Notion API密钥或数据库ID未配置"
    
    return True, "Notion配置有效"

def check_openai_config():
    """检查OpenAI环境变量配置是否有效"""
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    # 检查是否为空
    if not openai_api_key:
        return False, "OpenAI API密钥未配置"
    
    return True, "OpenAI配置有效"

def check_imgur_config():
    """检查Imgur环境变量配置是否有效"""
    imgur_client_id = os.getenv("IMGUR_CLIENT_ID", "")
    
    # 检查是否为空
    if not imgur_client_id:
        return False, "Imgur Client ID未配置"
    
    return True, "Imgur配置有效"

def check_images_without_imgur_url(data):
    """检查是否有图片没有上传到Imgur"""
    missing_imgur = []
    for item in data:
        # 检查是否有原始图片URL但没有Imgur URL
        if item.get("original_image_url") and not item.get("imgur_url"):
            missing_imgur.append(item)
    return missing_imgur

def check_module_exists(module_name):
    """检查模块是否存在"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def main():
    """执行完整工作流程"""
    logger.info("开始执行小红书内容生成工作流")
    
    # 前置检查
    if not check_module_exists("llm"):
        logger.error("缺少必要的llm模块")
        logger.info("解决方案: 请确保项目根目录下存在llm目录，且包含必要的模块文件")
        logger.info("1. 创建llm目录: mkdir -p llm")
        logger.info("2. 创建必要的文件: __init__.py, langchain_utils.py, models.py")
        return
    
    workflow_results = {
        "workflow_name": "小红书内容生成",
        "start_time": datetime.now().isoformat(),
        "steps": []
    }
    
    # 步骤1: 抓取趋势和新闻
    step1_success = run_command("python stages/fetch_trends.py", "抓取趋势和新闻")
    workflow_results["steps"].append({
        "name": "抓取趋势和新闻",
        "success": step1_success,
        "timestamp": datetime.now().isoformat()
    })
    
    if not step1_success:
        logger.error("❌ 趋势抓取失败，停止工作流程")
        workflow_results["end_time"] = datetime.now().isoformat()
        workflow_results["overall_status"] = "失败"
        log_workflow_results("xhs_workflow", workflow_results)
        return
    
    # 步骤2: 使用LangChain生成内容
    step2_success = run_command("python stages/generate_content_langchain.py", "使用LangChain生成内容")
    workflow_results["steps"].append({
        "name": "使用LangChain生成内容",
        "success": step2_success,
        "timestamp": datetime.now().isoformat()
    })
    
    if not step2_success:
        logger.error("❌ 内容生成失败，停止工作流程")
        workflow_results["end_time"] = datetime.now().isoformat()
        workflow_results["overall_status"] = "失败"
        log_workflow_results("xhs_workflow", workflow_results)
        return
    
    # 步骤3: 统计生成的内容
    generated_content = []
    try:
        with open("data/generated_langchain_content.json", "r", encoding="utf-8") as f:
            generated_content = json.load(f)
        
        logger.info(f"\n📊 内容生成统计:")
        logger.info(f"总计生成 {len(generated_content)} 条内容")
        
        # 显示生成的内容标题
        for i, content in enumerate(generated_content, 1):
            logger.info(f"{i}. {content.get('title', '无标题')}")
        
        workflow_results["content_count"] = len(generated_content)
        workflow_results["overall_status"] = "成功"
    except Exception as e:
        log_error(logger, f"统计结果失败: {e}")
        workflow_results["overall_status"] = "部分成功"
        if not generated_content:
            logger.warning("没有内容可处理，跳过后续步骤")
            workflow_results["end_time"] = datetime.now().isoformat()
            log_workflow_results("xhs_workflow", workflow_results)
            return
    
    # 步骤4: 生成图片并上传到Imgur
    openai_config_valid, openai_config_message = check_openai_config()
    if not openai_config_valid:
        logger.warning(f"\n⚠️ {openai_config_message}")
        logger.warning("⏩ 跳过图片生成步骤 - 请先设置OPENAI_API_KEY环境变量")
        workflow_results["steps"].append({
            "name": "生成图片并上传到Imgur",
            "success": False,
            "skipped": True,
            "reason": openai_config_message,
            "timestamp": datetime.now().isoformat()
        })
    else:
        step4_success = run_command("python stages/generate_image.py", "生成图片并上传到Imgur")
        workflow_results["steps"].append({
            "name": "生成图片并上传到Imgur",
            "success": step4_success,
            "timestamp": datetime.now().isoformat()
        })
        
        if not step4_success:
            logger.warning("⚠️ 图片生成失败，但将继续工作流程")
    
    # 步骤4.5: 检查是否需要单独上传图片到Imgur
    image_data = []
    try:
        if os.path.exists("data/image_content.json"):
            with open("data/image_content.json", "r", encoding="utf-8") as f:
                image_data = json.load(f)
            
            # 检查是否有图片没有上传到Imgur
            missing_imgur = check_images_without_imgur_url(image_data)
            if missing_imgur and upload_to_imgur:
                logger.info(f"\n发现 {len(missing_imgur)} 张图片未上传到Imgur，尝试单独上传...")
                
                # 检查Imgur配置
                imgur_config_valid, imgur_config_message = check_imgur_config()
                if not imgur_config_valid:
                    logger.warning(f"⚠️ {imgur_config_message}")
                    logger.warning("⏩ 跳过Imgur上传步骤 - 请先设置IMGUR_CLIENT_ID环境变量")
                else:
                    # 调用单独的Imgur上传功能
                    log_stage_start(logger, "单独上传图片到Imgur")
                    start_time = time.time()
                    imgur_success = upload_to_imgur()
                    
                    if imgur_success:
                        log_stage_end(logger, "单独上传图片到Imgur", success=True, duration=time.time() - start_time)
                        # 重新加载更新后的数据
                        with open("data/image_content.json", "r", encoding="utf-8") as f:
                            image_data = json.load(f)
                    else:
                        log_stage_end(logger, "单独上传图片到Imgur", success=False, duration=time.time() - start_time)
                        logger.warning("⚠️ 单独上传图片到Imgur失败，但将继续工作流程")
                
                workflow_results["steps"].append({
                    "name": "单独上传图片到Imgur",
                    "success": imgur_success if 'imgur_success' in locals() else False,
                    "timestamp": datetime.now().isoformat()
                })
    except Exception as e:
        log_error(logger, f"检查Imgur上传状态时出错: {e}")
    
    # 步骤5: 推送到Notion
    notion_success = False
    
    # 检查Notion配置
    notion_config_valid, notion_config_message = check_notion_config()
    if not notion_config_valid:
        logger.warning(f"\n⚠️ {notion_config_message}")
        logger.warning("⏩ 跳过推送到Notion步骤 - 请先设置NOTION_API_KEY和NOTION_DATABASE_ID环境变量")
        workflow_results["steps"].append({
            "name": "推送内容到Notion",
            "success": False,
            "skipped": True,
            "reason": notion_config_message,
            "timestamp": datetime.now().isoformat()
        })
    elif push_to_notion and generated_content:
        log_stage_start(logger, "推送内容到Notion")
        start_time = time.time()
        
        try:
            # 尝试读取带图片的内容
            image_content_path = "data/image_content.json"
            if os.path.exists(image_content_path):
                try:
                    with open(image_content_path, "r", encoding="utf-8") as f:
                        notion_ready_content = json.load(f)
                    logger.info(f"✅ 使用带图片的内容数据 ({len(notion_ready_content)} 条)")
                except Exception as e:
                    log_error(logger, f"读取图片内容数据失败: {e}，将使用原始内容")
                    notion_ready_content = prepare_content_for_notion(generated_content)
            else:
                logger.warning("⚠️ 未找到图片内容数据，将使用原始内容")
                notion_ready_content = prepare_content_for_notion(generated_content)
            
            # 调用推送功能
            success_count, error_count = push_to_notion(notion_ready_content)
            
            notion_success = success_count > 0
            workflow_results["steps"].append({
                "name": "推送内容到Notion",
                "success": notion_success,
                "success_count": success_count,
                "error_count": error_count,
                "timestamp": datetime.now().isoformat()
            })
            
            log_stage_end(logger, "推送内容到Notion", success=notion_success, duration=time.time() - start_time)
            logger.info(f"成功: {success_count} 条, 失败: {error_count} 条")
        except Exception as e:
            log_error(logger, f"推送到Notion失败: {e}")
            log_stage_end(logger, "推送内容到Notion", success=False, duration=time.time() - start_time)
            workflow_results["steps"].append({
                "name": "推送内容到Notion",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    else:
        logger.warning("\n⏩ 跳过推送到Notion步骤 - 模块未导入或无内容可推送")
        workflow_results["steps"].append({
            "name": "推送内容到Notion",
            "success": False,
            "skipped": True,
            "reason": "模块未导入或无内容可推送",
            "timestamp": datetime.now().isoformat()
        })
    
    # 完成工作流程
    workflow_results["end_time"] = datetime.now().isoformat()
    log_workflow_results("xhs_workflow", workflow_results)
    
    # 打印完成信息
    logger.info("\n🎉 工作流程执行完成!")
    if notion_success:
        logger.info("✅ 内容已成功推送到Notion")
    else:
        logger.warning("⚠️ 内容未能成功推送到Notion")
        if not notion_config_valid:
            logger.info("📝 要启用Notion推送功能，请设置以下环境变量:")
            logger.info('  - NOTION_API_KEY: Notion API密钥')
            logger.info('  - NOTION_DATABASE_ID: Notion数据库ID')

if __name__ == "__main__":
    main() 