import json
import openai
from utils.load_config import load_all_config

# Load configuration
config = load_all_config()
client = openai.OpenAI(api_key=config["openai_api_key"])

def call_gpt_with_system(prompt, system_message, model="gpt-4", temperature=0.7):
    """Call GPT with a system message to enforce strict formatting"""
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()

def test_json_formatting():
    # 加载测试数据
    with open("data/news_content.json", "r") as f:
        news_data = json.load(f)
        test_item = news_data[0]
    
    # 简化的事实摘要 (通常由前一步生成)
    fact_summary = """
2025年2月27日，加拿大对快速通道类别进行了改动，贸易类别新增了19个职业，同时删除了4个职业，使得现在贸易类别总共包含25个职业。
改动后，只要在符合类别的职业中有至少六个月的全职连续工作经验（或相等的兼职经验），并满足快速通道的最低标准，就有资格获得贸易类别的抽签资格。
若符合类别抽签资格，将有更大机会收到申请加拿大永久居留权的邀请，即使CRS分数较低。
例如，2024年，普通抽签的CRS分数要求在524到549之间，而贸易类别的CRS分数要求在433到436之间。
    """
    
    # 定义严格的系统消息来强制JSON格式
    system_message = """
你是一个专门的JSON响应生成器。你的输出必须是有效的JSON对象，格式完全符合要求，不添加任何注释或额外文本。
你必须遵循以下规则：
1. 输出必须是纯粹的JSON对象，不包含任何其他文本
2. 输出必须以左大括号"{"开始，以右大括号"}"结束
3. 所有键和字符串值必须使用双引号，不能使用单引号
4. 不添加markdown代码块（如```json）或其他格式标记
5. 不包含任何前言或后语解释
6. 不包含中文标点如【】、「」等

违反这些规则将被视为完全失败，所以请严格遵守。
"""

    # 用户提示词
    user_prompt = f"""
请根据以下提供的事实摘要，生成一篇关于加拿大移民的小红书爆款文案：

{fact_summary}

返回JSON必须严格符合以下格式：

{{
  "title": "抓住读者注意力的核心爆点，10-15字",
  "headline": "补充标题信息并引发好奇，15-25字",
  "content": "正文内容（夸张风格，结合事实总结，添加推理、观点、情绪张力，以互动语气结尾）",
  "image_keywords": ["关键词1", "关键词2", "关键词3"],
  "cover_prompt": "用于生成封面图的详细描述"
}}
"""

    print("正在调用API获取JSON格式内容...")
    result = call_gpt_with_system(user_prompt, system_message)
    
    print("\n== LLM原始返回 ==")
    print(result)
    print(f"返回结果长度: {len(result)} 字符")
    print(f"返回结果前20个字符: '{result[:20]}'")
    print(f"返回结果后20个字符: '{result[-20:]}'")
    
    # 检查是否包含常见非JSON标记
    markers = ["【", "】", "```json", "```", "JSON:", "json:"]
    for marker in markers:
        if marker in result:
            print(f"警告: 返回结果包含非JSON标记 '{marker}'")
    
    # 尝试解析JSON
    print("\n尝试解析JSON...")
    try:
        result_json = json.loads(result)
        print("JSON解析成功!")
        print(json.dumps(result_json, ensure_ascii=False, indent=2))
        
        # 保存成功解析的JSON
        with open("data/generated_content.json", "w", encoding="utf-8") as f:
            json.dump(result_json, ensure_ascii=False, indent=2, fp=f)
        print("已保存到 data/generated_content.json")
        return True
        
    except Exception as e:
        print(f"JSON解析失败: {e}")
        
        # 尝试简单的预处理和修复
        try:
            # 移除可能的前缀和后缀文本
            import re
            json_pattern = r'({[\s\S]*})'
            match = re.search(json_pattern, result)
            if match:
                potential_json = match.group(1)
                # 替换单引号为双引号
                potential_json = potential_json.replace("'", '"')
                result_json = json.loads(potential_json)
                print("预处理后JSON解析成功!")
                print(json.dumps(result_json, ensure_ascii=False, indent=2))
                
                # 保存成功解析的JSON
                with open("data/generated_content.json", "w", encoding="utf-8") as f:
                    json.dump(result_json, ensure_ascii=False, indent=2, fp=f)
                print("已保存到 data/generated_content.json")
                return True
        except Exception as e2:
            print(f"预处理后仍然解析失败: {e2}")
            return False

if __name__ == "__main__":
    test_json_formatting() 