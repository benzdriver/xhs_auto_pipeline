import os
import json
from llm.call_gpt import smart_llm_call
from constants import PLATFORMS



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
        return text.replace("疯人院", "枫人院")
    return text

def run(news_data, channel="枫人院的放大镜", platform=PLATFORMS[0], save_to_json=False):
    outputs = []
    all_prompts_and_responses = []
    for item in news_data:
        title = item["title"]
        url = item["url"]
        summary = item.get("summary") or ""
        source = item["source"]
        ranking = item["ranking"]
        full_content = item.get("full_content") or ""
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
        xhs_block_prompt = """
你是疯人院的爆料记者，风格夸张、脑洞大、敢于推理和深度解读。请用疯人院独家视角，结合以下事实总结，输出一篇小红书爆款文案，要求：
- 不仅总结新闻事实，还要大胆推测背后原因、影响和趋势
- 必须引用事实总结中的具体数据、细节、官方表述，并用疯人院风格解读
- 可以适当脑补细节、用夸张修辞、制造悬念、引发讨论
- 内容要有故事感、情绪张力和独家观点
- 结尾用疯人院式互动语气，鼓励评论和转发

【事实总结】
{block}
"""
        xhs_merge_prompt = """
请综合以下所有分块疯人院推理，生成最终小红书爆款文案，输出如下结构化 JSON：
{fact_summary}
{
  "title": "疯人院爆款标题（夸张、吸睛、带悬念）",
  "headline": "副标题/描述（可选，疯人院风格）",
  "content": "正文内容（疯人院独家视角，结合事实总结，夸张推理、脑洞补充、独家观点、故事感、情绪张力，结尾疯人院式互动语气）",
  "image_keywords": ["关键词1", "关键词2"]
}
【注意】image_keywords 必须至少包含2个与内容高度相关的关键词，不能为空。
"""
        xhs_result, xhs_prompts = smart_llm_call(
            fact_summary,
            block_prompt_template=xhs_block_prompt,
            merge_prompt_template=xhs_merge_prompt
        )
        # 尝试解析 LLM 返回的 JSON
        try:
            result_json = json.loads(xhs_result)
            title = result_json.get("title", "")
            headline = result_json.get("headline", "")
            content = result_json.get("content", "")
            image_keywords = result_json.get("image_keywords", [])
            # fallback: 如果 image_keywords 为空，用 title 拆分关键词
            if not image_keywords or not any(image_keywords):
                image_keywords = [w for w in title.replace('，',',').replace('、',',').replace(' ',',').split(',') if w][:2]
        except Exception:
            title = item["title"]
            headline = ""
            content = xhs_result
            # fallback: 用 title 拆分关键词
            image_keywords = [w for w in title.replace('，',',').replace('、',',').replace(' ',',').split(',') if w][:2]
        outputs.append({
            "title": replace_fengrenyuan(title),
            "headline": replace_fengrenyuan(headline),
            "url": url,
            "summary": replace_fengrenyuan(summary),
            "source": source,
            "ranking": ranking,
            "channel": channel,
            "content": replace_fengrenyuan(content),
            "image_keywords": [replace_fengrenyuan(k) for k in image_keywords],
            "platform": platform,
            "types": [platform]
        })
        all_prompts_and_responses.append({
            "title": title,
            "fact_prompts": fact_prompts,
            "xhs_prompts": xhs_prompts
        })
    if save_to_json:
        os.makedirs("data", exist_ok=True)
        with open("data/generated_content.json", "w") as f:
            json.dump(outputs, f, ensure_ascii=False, indent=2)
        with open("data/generated_content_prompts.json", "w") as f:
            json.dump(all_prompts_and_responses, f, ensure_ascii=False, indent=2)
    return outputs

if __name__ == "__main__":
    import json
    news_path = "data/news_content.json"
    if not os.path.exists(news_path):
        print(f"[ERROR] {news_path} 不存在，请先运行 fetch_trends 阶段。")
    else:
        with open(news_path, "r") as f:
            news_data = json.load(f)
        news_data = news_data[:3]  # 只取前3条新闻
        print(f"[INFO] 加载 {len(news_data)} 条新闻，开始生成内容...")
        outputs = run(news_data, save_to_json=True)
        print(f"[INFO] 已生成 {len(outputs)} 条内容，已保存到 data/generated_content.json")