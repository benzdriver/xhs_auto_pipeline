import os
import json
from llm.call_gpt import smart_llm_call
from constants import PLATFORMS
from utils.cache_utils import get_unprocessed_news, mark_batch_processed, is_news_processed_by_stage
import hashlib
from datetime import datetime
import sys
import time
import random
from tqdm import tqdm

# 添加父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added parent directory to PYTHONPATH: {parent_dir}")

# 通用 Channel Prompt 模板
CHANNEL_PROMPT_TEMPLATE = """
你是{channel_name}的内容策划，{channel_desc}
你的任务是：
- 参考输入的新闻摘要和图片链接，生成一则{platform}爆款内容
- 内容风格：{style}
- 必须引用新闻事实，内容真实、专业、有故事感
- 如果有图片链接，保留图片链接，作为配图推荐
- 结尾加一句引导互动的话

【频道背景】
{channel_background}
"""

# 疯人院风格指南
FENGRENYUAN_STYLE = """
疯人院风格指南:
- 标题必须吸睛、带有爆点、制造悬念，用词夸张但不失可信度
- 副标题要有共鸣、反转或关键信息，引导继续阅读
- 内容风格大胆、有独家视角、敢于推理和猜测
- 口吻犀利、幽默、有温度，仿佛在对读者"爆料"
- 必须包含一些夸张修辞或疯人院特色用语（如"重磅""独家""内幕""绝了"等）
- 在保持专业性的同时，加入感性和情绪化表达
"""

# 频道信息（可扩展）
CHANNELS = {
    "枫人院的放大镜": {
        "desc": "专门搜集加拿大移民资讯、新闻、重大政策改动。",
        "background": "枫人院的放大镜是一个专注于加拿大移民领域的内容频道，致力于为用户提供最新、最权威的移民政策、新闻解读和实用信息。",
        "platform": "小红书",
        "style": "吸睛、共鸣、故事感、专业、可信、温暖"
    },
    # 未来可扩展更多频道
}

def is_valid_summary(summary):
    summary = summary.strip()
    # 过滤只有链接、只有表格、只有"点击申请"等无效内容
    if len(summary) < 30:
        return False
    if summary.count('<a href=') > 0 and len(summary) < 80:
        return False
    if any(x in summary for x in ['点击申请', '下载表格', 'application form', 'apply now', 'download', '表格', '申请表', 'guide', '指南']):
        return False
    return True

def replace_fengrenyuan(text):
    if isinstance(text, str):
        return text.replace("疯人", "枫人")
    return text

def run(news_data=None, channel="枫人院的放大镜", platform=PLATFORMS[0], save_to_json=False):
    outputs = []
    all_prompts_and_responses = []
    
    # 如果没有传入news_data，从news_content.json读取
    if news_data is None:
        try:
            with open("data/news_content.json", "r") as f:
                news_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] 读取news_content.json失败: {e}")
            return []
    
    # 获取未处理的新闻
    unprocessed_news = get_unprocessed_news("generate_content")
    if not unprocessed_news:
        print("[INFO] 没有新的新闻需要处理")
        return []
    
    print(f"[INFO] 发现 {len(unprocessed_news)} 条未处理的新闻")
    
    # 只处理未处理的新闻
    for item in unprocessed_news:
        title = item["title"]
        url = item["url"]
        summary = item.get("summary") or ""
        source = item["source"]
        ranking = item["ranking"]
        full_content = item.get("full_content") or ""
        news_id = item.get("id", hashlib.md5(url.encode()).hexdigest()[:8])
        publish_date = item.get("publish_date")
        
        # 优先用 full_content
        if full_content and len(full_content) > 200:
            news_input = full_content
            print(f"[DEBUG] 用 full_content 生成，长度: {len(full_content)}")
        else:
            if is_valid_summary(summary):
                news_input = summary
                print(f"[DEBUG] 用 summary 生成，长度: {len(summary)}")
            else:
                print(f"[WARN] 无有效正文和摘要，跳过该新闻: {title}")
                continue
        print(f"[DEBUG] 输入新闻标题: {title}")
        print(f"[DEBUG] 输入正文片段: {news_input[:200]}...\n")
        
        # 步骤1：事实总结
        fact_block_prompt = """
请用简明扼要的中文，总结以下新闻原文中的关键事实、数据、政策变化、官方表述和细节：

【正文分块{idx}/{total}】
{block}

【事实总结】
"""
        fact_merge_prompt = """
请综合以下所有分块摘要，生成一份完整的事实总结：
{fact_summary}
【完整事实总结】
"""
        fact_summary, fact_prompts = smart_llm_call(
            news_input,
            block_prompt_template=fact_block_prompt,
            merge_prompt_template=fact_merge_prompt
        )
        # 步骤2：疯人院推理
        xhs_block_prompt = f"""
你是枫人院的爆料记者，风格夸张、脑洞大、敢于推理和深度解读。请用枫人院独家视角，结合以下事实总结，输出一篇小红书爆款文案，满足以下要求：

{FENGRENYUAN_STYLE}

【事实总结】
{{block}}

【新闻背景信息】
- 新闻标题：{title}
- 新闻来源：{source}
- 发布时间：{publish_date or '最近'}
"""
        
        xhs_merge_prompt = """
请综合以下所有分块枫人院推理，生成最终小红书爆款文案，确保标题极具吸引力。请务必以标准JSON格式输出，格式如下：
{fact_summary}

{{
  "title": "「超吸睛标题」抓住读者注意力的核心爆点，10-15字",
  "headline": "「副标题」补充标题信息并引发好奇，15-25字",
  "content": "正文内容（枫人院独家视角，结合事实总结，夸张推理、脑洞补充、独家观点、情绪张力，结尾互动语气）",
  "image_keywords": ["关键词1", "关键词2", "关键词3"],
  "cover_prompt": "用于生成封面图的详细描述，结合标题和关键词，强调视觉冲击力"
}}

【重要】必须只输出一个有效的JSON对象，不要有任何其他前缀或后缀文本。确保所有引号和大括号匹配正确。
image_keywords必须包含3-5个与内容高度相关且具视觉冲击力的关键词；
cover_prompt必须详细描述一个能抓住眼球的封面图。
"""
        
        xhs_result, xhs_prompts = smart_llm_call(
            fact_summary,
            block_prompt_template=xhs_block_prompt,
            merge_prompt_template=xhs_merge_prompt
        )
        
        # 尝试解析 LLM 返回的 JSON
        try:
            # 调试信息：打印返回内容的前30个字符
            print(f"[DEBUG] LLM返回的前30个字符: '{xhs_result[:30]}'")
            result_json = json.loads(xhs_result)
            title = result_json.get("title", "")
            headline = result_json.get("headline", "")
            content = result_json.get("content", "")
            image_keywords = result_json.get("image_keywords", [])
            cover_prompt = result_json.get("cover_prompt", "")
            
            # fallback: 如果 image_keywords 为空，用 title 拆分关键词
            if not image_keywords or not any(image_keywords):
                image_keywords = [w for w in title.replace('，',',').replace('、',',').replace(' ',',').split(',') if w][:3]
        except Exception as e:
            print(f"[ERROR] 解析JSON失败: {e}")
            
            # 尝试从文本中提取信息
            import re
            
            # 尝试提取JSON部分
            json_pattern = r'({[\s\S]*})'
            match = re.search(json_pattern, xhs_result)
            if match:
                potential_json = match.group(1)
                try:
                    result_json = json.loads(potential_json)
                    title = result_json.get("title", "")
                    headline = result_json.get("headline", "")
                    content = result_json.get("content", "")
                    image_keywords = result_json.get("image_keywords", [])
                    cover_prompt = result_json.get("cover_prompt", "")
                except Exception:
                    # 如果JSON提取失败，回退到正则提取
                    title = item["title"]
                    headline = ""
                    content = xhs_result
                    
                    # 尝试从文本中提取标题和副标题
                    title_match = re.search(r'【标题】"?([^"\n]+)"?', xhs_result)
                    if title_match:
                        title = title_match.group(1)
                    
                    headline_match = re.search(r'【副标题】"?([^"\n]+)"?', xhs_result)
                    if headline_match:
                        headline = headline_match.group(1)
                    
                    # 尝试移除标题和副标题部分，只保留正文
                    content = re.sub(r'【标题】.*\n', '', content)
                    content = re.sub(r'【副标题】.*\n', '', content)
                    
                    # 提取文章中提到的关键词作为image_keywords
                    keywords_match = re.findall(r'([^，,、\s]{2,6})', title + " " + headline)
                    image_keywords = list(set(keywords_match))[:5]
                    cover_prompt = f"加拿大移民政策相关封面，标题：{title}"
            else:
                # 如果没有找到JSON格式，直接使用原始返回
                title = item["title"]
                headline = ""
                content = xhs_result
                # fallback: 用 title 拆分关键词
                image_keywords = [w for w in title.replace('，',',').replace('、',',').replace(' ',',').split(',') if w][:3]
                cover_prompt = f"加拿大移民政策相关封面，标题：{title}"
        
        # 创建输出项
        output_item = {
            "id": news_id,
            "title": replace_fengrenyuan(title),
            "headline": replace_fengrenyuan(headline),
            "url": url,
            "summary": replace_fengrenyuan(summary),
            "source": source,
            "ranking": ranking,
            "channel": channel,
            "content": replace_fengrenyuan(content),
            "image_keywords": [replace_fengrenyuan(k) for k in image_keywords],
            "cover_prompt": replace_fengrenyuan(cover_prompt),
            "platform": platform,
            "types": [platform],
            "original_publish_date": publish_date,
            "process_date": datetime.now().isoformat()
        }
        
        outputs.append(output_item)
        all_prompts_and_responses.append({
            "title": title,
            "fact_prompts": fact_prompts,
            "xhs_prompts": xhs_prompts
        })
    
    # 标记所有处理过的新闻
    mark_batch_processed(unprocessed_news, "generate_content")
    
    if save_to_json:
        os.makedirs("data", exist_ok=True)
        with open("data/generated_content.json", "w") as f:
            json.dump(outputs, f, ensure_ascii=False, indent=2)
        with open("data/generated_content_prompts.json", "w") as f:
            json.dump(all_prompts_and_responses, f, ensure_ascii=False, indent=2)
    
    return outputs

def generate_content_for_news(news_data, style="小红书", channel="枫人院"):
    """为单条新闻生成小红书内容"""
    # 提取新闻数据
    title = news_data.get("title", "无标题")
    content = news_data.get("full_content", news_data.get("summary", "无内容"))
    source = news_data.get("source", "未知来源")
    publish_date = news_data.get("publish_date", "近期")
    
    # 构建提示
    system_prompt = f"""
    你是一个专业的加拿大移民顾问和小红书爆款写手。
    你的任务是将一篇关于加拿大移民的新闻或资讯改写为{style}平台上的爆款内容。
    输出必须是JSON格式，包含以下字段：
    - title: 吸引人的标题，10-15字
    - headline: 内容摘要，20-30字
    - content: 正文内容，至少500字
    - image_keywords: 用于生成封面图片的5个关键词
    - tags: 3-5个相关标签
    """
    
    user_prompt = f"""
    请把以下新闻改写成{style}平台"{channel}"账号的爆款内容：
    
    标题：{title}
    来源：{source}
    发布时间：{publish_date}
    
    正文：
    {content[:2000]}  # 限制长度以避免token超限
    
    要求：
    1. 使用枫人院特色的爆料风格，大胆、夸张但不失真实性
    2. 添加移民顾问的专业解读和分析
    3. 用生动的比喻和隐喻解释复杂的移民政策
    4. 加入互动元素，如"你们觉得呢？"等鼓励互动的问句
    5. 正文内容必须丰富详实，不少于500字
    6. 输出必须是有效的JSON格式
    
    JSON格式如下：
    ```json
    {
        "title": "吸引人的标题",
        "headline": "内容摘要",
        "content": "正文内容",
        "image_keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
        "tags": ["标签1", "标签2", "标签3"]
    }
    ```
    """
    
    try:
        # 使用我们的smart_llm_call函数调用API
        response = smart_llm_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4",
            output_format="json",
            temperature=0.8,
            max_tokens=2000
        )
        
        # 验证响应内容
        if not response or not isinstance(response, dict):
            raise ValueError(f"API返回的不是有效的JSON对象: {response}")
        
        # 检查必要字段
        required_fields = ["title", "headline", "content", "image_keywords"]
        for field in required_fields:
            if field not in response:
                raise ValueError(f"返回的JSON缺少必要字段: {field}")
        
        # 添加原始信息
        response["original_title"] = title
        response["original_source"] = source
        response["original_publish_date"] = publish_date
        
        # 如果没有tags字段，添加一个默认值
        if "tags" not in response:
            response["tags"] = ["加拿大移民", "移民政策", "枫人院分析"]
            
        # 确保content长度符合要求
        if len(response["content"]) < 500:
            print(f"警告: 生成的内容长度不足500字 ({len(response['content'])}字)")
        
        return response
        
    except Exception as e:
        print(f"生成内容时出错: {e}")
        # 返回一个简单的错误响应
        return {
            "title": title,
            "headline": f"处理{title}时出错",
            "content": f"生成内容时发生错误: {str(e)}",
            "image_keywords": ["错误", "加拿大", "移民", "资讯", "枫人院"],
            "tags": ["加拿大移民", "移民政策", "枫人院分析"],
            "original_title": title,
            "original_source": source, 
            "original_publish_date": publish_date,
            "error": str(e)
        }

def process_all_news(news_list, output_file="data/generated_content.json"):
    """处理所有新闻并保存结果"""
    print(f"开始处理 {len(news_list)} 条新闻...")
    results = []
    
    # 使用tqdm显示进度
    for i, news in enumerate(tqdm(news_list, desc="生成内容")):
        print(f"\n正在处理第 {i+1}/{len(news_list)} 条: {news.get('title', '无标题')}")
        
        # 生成内容
        result = generate_content_for_news(news)
        results.append(result)
        
        # 简单显示结果摘要
        print(f"标题: {result.get('title', '无标题')}")
        content_preview = result.get('content', '无内容')[:100] + '...' if result.get('content') else '无内容'
        print(f"内容预览: {content_preview}")
        
        # 添加随机延时，避免API限制
        if i < len(news_list) - 1:  # 最后一个不需要延时
            delay = random.uniform(1, 3)
            print(f"等待 {delay:.1f} 秒...")
            time.sleep(delay)
    
    # 保存结果到文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成，共生成 {len(results)} 条内容，已保存到 {output_file}")
    return results

if __name__ == "__main__":
    # 读取新闻数据
    with open("data/news_content.json", "r", encoding="utf-8") as f:
        news_list = json.load(f)
    
    # 处理所有新闻（此处可以切片减少处理数量）
    news_subset = news_list  # 如需测试，可改为 news_list[:3]
    process_all_news(news_subset)