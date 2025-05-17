import json
import sys
import re  # Add explicit import for regex
from llm.call_gpt import smart_llm_call
from stages.generate_content import FENGRENYUAN_STYLE

# 测试单个新闻内容生成
def test_single_news():
    # 加载第一条新闻
    with open("data/news_content.json", "r") as f:
        news_data = json.load(f)
        test_item = news_data[0]
    
    # 打印新闻信息
    print(f"测试新闻标题: {test_item['title']}")
    
    # 使用 summary 或 full_content
    news_input = test_item.get("full_content", "") or test_item.get("summary", "")
    if not news_input:
        print("错误: 新闻没有内容!")
        return
    
    print(f"新闻内容长度: {len(news_input)} 字符")
    
    # 步骤1: 事实总结
    fact_block_prompt = """
请用简明扼要的中文，总结以下新闻原文中的关键事实、数据、政策变化、官方表述和细节：

【正文分块{idx}/{total}】
{block}

【注意】如果这不是最后一个分块(即{idx}<{total})，请等待接收完所有分块后再生成最终摘要。现在请处理并记住此分块内容。

【事实总结】
"""
    fact_merge_prompt = """
请综合以下所有分块摘要，生成一份完整的事实总结：

{fact_summary}

【完整事实总结】
"""
    
    print("生成事实总结...")
    fact_summary, fact_prompts = smart_llm_call(
        news_input,
        block_prompt_template=fact_block_prompt,
        merge_prompt_template=fact_merge_prompt
    )
    
    print("\n== 事实总结 ==")
    print(fact_summary)
    print(f"事实总结长度: {len(fact_summary)} 字符")
    
    # 步骤2: 枫人院风格生成 (使用更明确的JSON格式指令)
    title = test_item["title"]
    source = test_item["source"]
    publish_date = test_item.get("publish_date", "最近")
    
    xhs_block_prompt = f"""
你是枫人院的爆料记者，风格夸张、脑洞大、敢于推理和深度解读。
请根据以下事实总结，提出一些小红书爆款内容的关键点和亮点：

{FENGRENYUAN_STYLE}

【事实总结分块{{idx}}/{{total}}】
{{block}}

【新闻背景信息】
- 新闻标题：{title}
- 新闻来源：{source}
- 发布时间：{publish_date}

【注意】如果这不是最后一个分块(即{{idx}}<{{total}})，请等待接收完所有分块后再生成最终内容。现在请处理并记住此分块内容。

【推理亮点】
"""
    
    xhs_merge_prompt = """
你是JSON编写专家。你的任务是输出一个有效的JSON对象，其中包含小红书文案信息。

【严格要求】
1. 你必须只输出一个有效的JSON对象，不要输出任何其他内容
2. 不要包含任何前言、解释或后语
3. 不要使用markdown代码块或任何其他格式标记
4. 不要包含"【】"等中文标记符号
5. 必须使用双引号而非单引号作为JSON键值对的定界符
6. 输出必须以左大括号"{"开始，以右大括号"}"结束

根据以下提供的信息，生成一篇小红书爆款文案：

{fact_summary}

返回JSON必须严格符合以下格式：

{
  "title": "「超吸睛标题」抓住读者注意力的核心爆点，10-15字",
  "headline": "「副标题」补充标题信息并引发好奇，15-25字",
  "content": "正文内容（枫人院独家视角，结合事实总结，夸张推理、脑洞补充、独家观点、情绪张力，结尾互动语气）",
  "image_keywords": ["关键词1", "关键词2", "关键词3"],
  "cover_prompt": "用于生成封面图的详细描述，结合标题和关键词，强调视觉冲击力"
}
"""
    
    print("\n生成枫人院风格内容（加强JSON格式要求）...")
    print("\n== 合并提示词 ==")
    print(xhs_merge_prompt.replace("{fact_summary}", "[事实总结内容]"))
    
    # 使用系统消息强制JSON格式
    system_message = """你是一个严格的JSON生成器。你只会生成有效的JSON，不会输出任何其他内容。
你的输出必须以"{"开始，以"}"结束，中间是有效的JSON内容。
不要使用markdown代码块，不要添加解释或注释。"""
    
    # 修改smart_llm_call以添加系统消息支持，如果该函数支持system_message参数
    xhs_result, xhs_prompts = smart_llm_call(
        fact_summary,
        block_prompt_template=xhs_block_prompt,
        merge_prompt_template=xhs_merge_prompt
    )
    
    print("\n== LLM原始返回 ==")
    print(xhs_result)
    print(f"返回结果长度: {len(xhs_result)} 字符")
    print(f"返回结果前20个字符: '{xhs_result[:20]}'")
    print(f"返回结果后20个字符: '{xhs_result[-20:]}'")
    
    # 检查是否包含常见非JSON标记
    markers = ["【", "】", "```json", "```", "JSON:", "json:"]
    for marker in markers:
        if marker in xhs_result:
            print(f"警告: 返回结果包含非JSON标记 '{marker}'")
    
    # 尝试解析JSON
    print("\n尝试解析JSON...")
    try:
        result_json = json.loads(xhs_result)
        print("JSON解析成功!")
        print(json.dumps(result_json, ensure_ascii=False, indent=2))
        
        # 保存成功解析的JSON
        with open("data/generated_content.json", "w", encoding="utf-8") as f:
            json.dump(result_json, ensure_ascii=False, indent=2, fp=f)
        print("已保存到 data/generated_content.json")
        
    except Exception as e:
        print(f"JSON解析失败: {e}")
        print("尝试预处理后解析...")
        
        # 尝试提取可能的JSON部分
        json_pattern = r'({[\s\S]*})'
        match = re.search(json_pattern, xhs_result)
        if match:
            potential_json = match.group(1)
            print("提取的JSON内容:")
            print(potential_json)
            print(f"提取JSON长度: {len(potential_json)} 字符")
            try:
                result_json = json.loads(potential_json)
                print("提取后JSON解析成功!")
                print(json.dumps(result_json, ensure_ascii=False, indent=2))
                
                # 保存成功解析的JSON
                with open("data/generated_content.json", "w", encoding="utf-8") as f:
                    json.dump(result_json, ensure_ascii=False, indent=2, fp=f)
                print("已保存到 data/generated_content.json")
                
            except Exception as e2:
                print(f"提取后JSON解析仍然失败: {e2}")
                
                # 添加更多处理尝试和调试信息
                print("\n== 尝试修复常见JSON问题 ==")
                cleaned_json = potential_json
                
                # 替换单引号为双引号
                if "'" in cleaned_json:
                    print("尝试将单引号替换为双引号...")
                    cleaned_json = cleaned_json.replace("'", '"')
                
                # 处理换行符和制表符等
                cleaned_json = cleaned_json.replace("\n", "\\n").replace("\t", "\\t")
                
                # 删除可能出现在JSON前后的非法字符
                cleaned_json = cleaned_json.strip()
                if not cleaned_json.startswith("{"):
                    print("修复: JSON不是以{开始")
                    start_idx = cleaned_json.find("{")
                    if start_idx >= 0:
                        cleaned_json = cleaned_json[start_idx:]
                
                if not cleaned_json.endswith("}"):
                    print("修复: JSON不是以}结束")
                    end_idx = cleaned_json.rfind("}")
                    if end_idx >= 0:
                        cleaned_json = cleaned_json[:end_idx+1]
                
                print("清理后的JSON:")
                print(cleaned_json)
                
                try:
                    result_json = json.loads(cleaned_json)
                    print("清理后JSON解析成功!")
                    print(json.dumps(result_json, ensure_ascii=False, indent=2))
                    
                    # 保存成功解析的JSON
                    with open("data/generated_content.json", "w", encoding="utf-8") as f:
                        json.dump(result_json, ensure_ascii=False, indent=2, fp=f)
                    print("已保存到 data/generated_content.json")
                    
                except Exception as e3:
                    print(f"清理后JSON解析仍然失败: {e3}")
                    print("原始响应可能不符合JSON格式，请检查LLM提示词")

if __name__ == "__main__":
    test_single_news() 