"""
示例：如何使用llm模块的LangChain功能
"""

import json
from llm.langchain_utils import ContentGenerator, get_content_generator, generate_fact_summary
from llm.models import XiaohongshuContent, WeiboContent

def example_generate_xiaohongshu_content():
    """示例：生成小红书内容"""
    # 准备示例新闻文本
    news_text = """
    Express Entry is prioritizing new trades: Do you qualify?
    
    If you qualify for Express Entry's new Trade category, you're more likely to receive an invitation to apply (ITA) for Canadian permanent residence.
    
    On February 27, 2025, Canada made major changes to its Express Entry categories.
    
    The Trade occupations category was overhauled with a total of 19 occupations added, and four removed.
    
    Eligible occupations under the new Trade category
    
    In 2025, the Trade category expanded more than any other, with the highest number of new occupations added. It now includes a total of 25 occupations.
    
    You can find the full list of occupations along with their corresponding National Occupation Classification (NOC) codes below, with the newly added occupations bolded.
    
    Occupation: Bricklayers, Cabinetmakers, Carpenters, Concrete finishers, Construction estimators, Construction managers, Construction millwrights and industrial mechanics
    
    How do Express Entry categories increase one's chances of gaining Canadian permanent residence?
    
    If you qualify for a category-based draw, you're more likely to receive an invitation to apply for PR through Express Entry.
    
    That's because you can be invited in a category-based draw with a significantly lower CRS score than for a general or Canadian Experience Class (CEC) draw.
    
    For example, in 2024, the CRS cut-off for general draws ranged between 524 and 549.
    
    However, in the same year, the CRS cut-off for Trade occupations ranged between 433 and 436.
    """
    
    # 1. 使用便捷函数生成事实摘要
    print("使用便捷函数生成事实摘要...")
    summary = generate_fact_summary(news_text)
    print(f"事实摘要: {summary}\n")
    
    # 2. 使用ContentGenerator实例
    print("使用ContentGenerator实例生成小红书内容...")
    generator = get_content_generator()
    
    # 准备上下文信息
    context = {
        "title": "Express Entry is prioritizing new trades: Do you qualify?",
        "source": "CIC News",
        "publish_date": "2025-02-28"
    }
    
    # 生成小红书内容
    xhs_content = generator.generate_structured_content(
        fact_summary=summary,
        output_structure=XiaohongshuContent,
        context=context,
        min_content_length=500
    )
    
    # 输出结果
    print("\n生成的小红书内容:")
    print(f"标题: {xhs_content.title}")
    print(f"副标题: {xhs_content.headline}")
    print(f"内容预览: {xhs_content.content[:200]}...")
    print(f"关键词: {xhs_content.image_keywords}")
    
    # 保存结果到文件
    result_dict = xhs_content.model_dump()
    with open("example_xiaohongshu_content.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    print("\n结果已保存到 example_xiaohongshu_content.json")
    
    return xhs_content

def example_generate_weibo_content():
    """示例：生成微博内容"""
    # 准备示例新闻文本
    news_text = """
    IRCC Update On Latest Processing Times As Of April 2025
    
    New IRCC Update: Canada's Immigration, Refugees, and Citizenship Canada (IRCC) rolled out fresh processing time updates on April 30, 2025, revealing timelines for visas, permanent residency (PR), and citizenship applications.
    
    Whether you're chasing a Canadian visa, PR card, or citizenship, these changes could impact your plans.
    
    Here's the scoop on the latest IRCC processing times, optimized for your next move.
    
    For over four years, we (INC – Immigration News Canada) have tracked IRCC data, keeping you in the loop.
    
    Since 2022, IRCC's revamped tool uses real-time stats for accurate estimates—ditching outdated standards.
    
    Now, updates drop monthly for citizenship, PR, and family sponsorships, while PR cards and temporary visas refresh weekly.
    """
    
    # 生成事实摘要
    generator = get_content_generator()
    summary = generator.generate_fact_summary(news_text)
    
    # 准备上下文信息
    context = {
        "title": "IRCC Update On Latest Processing Times",
        "source": "INC News",
        "publish_date": "2025-04-30"
    }
    
    # 定义微博内容生成提示
    weibo_prompt = """
    请根据以下信息，创作一条吸引人的微博内容：
    
    【事实摘要】
    {fact_summary}
    
    【要求】
    1. 内容简洁有力，不超过140字
    2. 包含1-2个政策要点和枫人院的独家观点
    3. 使用2-3个相关话题标签
    4. 语言风格要有情绪感染力
    """
    
    # 微博内容输出
    # 这里只是示例，需要自己实现微博内容生成逻辑
    print("微博内容生成功能待实现，请参考小红书内容生成逻辑自行实现")
    
    return None

if __name__ == "__main__":
    print("运行小红书内容生成示例...")
    example_generate_xiaohongshu_content()
    
    print("\n运行微博内容生成示例...")
    example_generate_weibo_content() 