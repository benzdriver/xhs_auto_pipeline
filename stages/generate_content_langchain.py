import json
import os
import sys
from typing import List, Dict, Any
import openai
from tqdm import tqdm
import time

# 添加父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added parent directory to PYTHONPATH: {parent_dir}")

# 导入我们新创建的模块
from llm.langchain_utils import ContentGenerator, generate_fact_summary
from llm.models import XiaohongshuContent
from utils.load_config import load_all_config
from utils.logger import get_logger, log_stage_start, log_stage_end, log_error
from utils.progress_indicator import ProgressIndicator, IndicatorType

# 初始化日志
logger = get_logger("generate_content_langchain")

# 加载配置
config = load_all_config()
openai.api_key = config["openai_api_key"]

# 枫人院风格定义
FENGRENYUAN_STYLE = """
枫人院爆料风格特点：
1. 夸张化解读：用更有戏剧性的描述来解释政策变动
2. 信息+观点：给出客观事实，但加入独到的解读和分析
3. 情绪化表达：使用感叹号、反问句等增加情绪张力
4. 比喻和类比：将复杂政策用通俗比喻解释
5. 强调独家视角：突出"枫人院独家"等标签，强调信息渠道的独特性
"""

def generate_basic_prompts(title: str, keywords: List[str] = None, content: str = None) -> Dict[str, str]:
    """生成基本的封面图片提示词，紧密结合内容
    
    Args:
        title: 内容标题
        keywords: 关键词列表
        content: 内容正文
        
    Returns:
        Dict: 包含中英文提示词的字典
    """
    if keywords is None or len(keywords) == 0:
        keywords = ["加拿大", "移民"]
    else:
        # 确保至少有"加拿大"和"移民"这两个关键词
        if "加拿大" not in keywords and "Canada" not in keywords:
            keywords.insert(0, "加拿大")
        if "移民" not in keywords and "immigration" not in keywords:
            keywords.insert(1, "移民")
    
    # 限制关键词数量
    keywords = keywords[:3]
    
    # 提取内容中的重要场景或元素
    scene_elements = []
    if content:
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
    
    # 构建中文提示词
    cover_prompt = f"为小红书平台创建一张关于加拿大移民的精美图片，主题是：{title}。"
    if keywords:
        cover_prompt += f" 图片应包含以下元素：{', '.join(keywords)}。"
    if scene_elements:
        cover_prompt += f" 建议场景：{', '.join(scene_elements)}。"
    
    # 构建详细的英文提示词，针对Diffusion模型优化
    # 提取标题的主题
    main_subject = title
    
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

KEY ELEMENTS TO INCLUDE:
- {', '.join(keywords)}
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
    
    return {
        "cover_prompt": cover_prompt,
        "cover_prompt_eng": cover_prompt_eng
    }

def generate_content(news_list, output_path="data/generated_langchain_content.json"):
    """使用LangChain处理一组新闻并生成内容"""
    logger.info(f"开始为 {len(news_list)} 条新闻生成内容...")
    
    # 创建存储目录
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 创建内容生成器
    content_generator = ContentGenerator(model_name="gpt-4", temperature=0.8)
    
    result_list = []
    error_count = 0
    
    # 处理每条新闻
    for i, news in enumerate(news_list):
        try:
            # 创建进度指示器
            news_title = news.get("title", f"新闻 #{i+1}")
            progress = ProgressIndicator(f"处理新闻: {news_title[:30]}...", IndicatorType.SPINNER, logger=logger)
            progress.start()
            
            # 使用summary或full_content
            news_input = news.get("full_content", "") or news.get("summary", "")
            if not news_input:
                logger.warning(f"新闻 #{i+1} 没有内容，跳过")
                progress.stop(f"新闻 #{i+1} 跳过 (没有内容)")
                continue
            
            # 1. 生成事实摘要
            logger.info(f"处理新闻 #{i+1}: {news['title']}")
            fact_summary = content_generator.generate_fact_summary(news_input)
            logger.info(f"事实摘要: {fact_summary[:100]}...")
            
            # 2. 准备上下文信息
            context = {
                "title": news["title"],
                "source": news["source"],
                "publish_date": news.get("publish_date", "最近")
            }
            
            # 3. 生成小红书内容
            xhs_content = content_generator.generate_structured_content(
                fact_summary=fact_summary,
                output_structure=XiaohongshuContent,
                context=context,
                style=FENGRENYUAN_STYLE,
                min_content_length=500
            )
            
            # 4. 转换为字典并添加原始信息
            if xhs_content:
                content_dict = xhs_content.model_dump()
                content_dict["original_title"] = news["title"]
                content_dict["original_source"] = news["source"]
                content_dict["original_publish_date"] = news.get("publish_date", "最近")
                
                # 5. 生成基本的封面提示词
                keywords = content_dict.get("image_keywords", [])
                prompts = generate_basic_prompts(
                    title=content_dict["title"], 
                    keywords=keywords,
                    content=content_dict.get("content", "")
                )
                content_dict["cover_prompt"] = prompts["cover_prompt"]
                content_dict["cover_prompt_eng"] = prompts["cover_prompt_eng"]
                
                # 添加到结果列表
                result_list.append(content_dict)
                progress.stop(f"成功生成内容: {content_dict['title'][:30]}...")
            else:
                error_count += 1
                progress.stop(f"无法为新闻 #{i+1} 生成有效内容")
            
        except Exception as e:
            log_error(logger, f"处理新闻 #{i+1} 时发生异常: {e}")
            error_count += 1
            if 'progress' in locals():
                progress.stop(f"处理新闻 #{i+1} 失败: {str(e)[:50]}...")
    
    # 创建保存进度指示器
    save_progress = ProgressIndicator("保存生成的内容", IndicatorType.DOTS, logger=logger)
    save_progress.start()
    
    # 保存结果
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_list, ensure_ascii=False, indent=2, fp=f)
        
        # 同时保存到标准输出路径以保持兼容性
        standard_output_path = "data/generated_content.json"
        with open(standard_output_path, "w", encoding="utf-8") as f:
            json.dump(result_list, ensure_ascii=False, indent=2, fp=f)
            
        save_progress.stop(f"内容已保存到 {output_path} 和 {standard_output_path}")
    except Exception as e:
        save_progress.stop(f"保存内容失败: {str(e)}")
        logger.error(f"保存内容时出错: {e}")
    
    logger.info(f"内容生成完成，共 {len(result_list)} 条成功，{error_count} 条失败")
    return result_list

if __name__ == "__main__":
    # 加载新闻列表
    log_stage_start(logger, "LangChain内容生成")
    start_time = time.time()
    
    try:
        # 创建加载进度指示器
        load_progress = ProgressIndicator("加载新闻数据", IndicatorType.PULSE, logger=logger)
        load_progress.start()
        
        try:
            with open("data/news_content.json", "r", encoding="utf-8") as f:
                news_list = json.load(f)
            load_progress.stop(f"成功加载 {len(news_list)} 条新闻")
        except Exception as e:
            load_progress.stop(f"加载新闻数据失败: {str(e)}")
            raise e
            
        # 测试处理前3条
        test_news = news_list[:3]
        
        # 总体进度指示器
        main_progress = ProgressIndicator("LangChain内容生成", IndicatorType.BOUNCE, logger=logger)
        main_progress.start()
        
        try:
            generate_content(test_news)
            main_progress.stop("LangChain内容生成完成")
        except Exception as e:
            main_progress.stop(f"LangChain内容生成失败: {str(e)}")
            raise e
            
        log_stage_end(logger, "LangChain内容生成", success=True, duration=time.time() - start_time)
    except Exception as e:
        log_error(logger, f"LangChain内容生成失败: {e}")
        log_stage_end(logger, "LangChain内容生成", success=False, duration=time.time() - start_time) 