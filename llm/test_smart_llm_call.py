"""
测试更新后的 smart_llm_call 函数
"""

import json
from llm.call_gpt import smart_llm_call

def test_smart_llm_call():
    """测试 smart_llm_call 函数"""
    
    # 测试文本 - 一个相对较长的加拿大移民政策文本
    test_text = """
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
    
    # 测试1：使用 {fact_summary} 格式的旧版模板（向后兼容）
    print("测试1: 使用旧版模板格式...")
    
    block_prompt_template = """
    请用简明扼要的中文，总结以下新闻原文块中的关键事实、数据、政策变化、官方表述和细节：
    
    【文本块 {idx}/{total}】
    {block}
    
    块摘要:
    """
    
    # 旧版格式使用 {fact_summary}
    merge_prompt_template = """
    请将以下多个文本块的摘要整合成一个连贯、完整的事实总结：
    
    {fact_summary}
    
    完整总结:
    """
    
    system_message = "你是一位专业的加拿大移民信息分析师，善于提取关键事实和数据。"
    
    result, process_info = smart_llm_call(
        text=test_text,
        block_prompt_template=block_prompt_template,
        merge_prompt_template=merge_prompt_template,
        system_message=system_message,
        max_retries=1
    )
    
    print(f"\n测试1结果: {result[:100]}...\n")
    print(f"处理过程中的步骤数: {len(process_info)}")
    print(f"总Token使用量: {sum(item.get('tokens', 0) for item in process_info)}")
    
    # 测试2：使用 {summaries} 格式的新版模板
    print("\n测试2: 使用新版模板格式...")
    
    # 新版格式使用 {summaries}
    new_merge_template = """
    请将以下多个文本块的摘要整合成一个连贯、完整的事实总结：
    
    {summaries}
    
    完整总结:
    """
    
    # 自定义后处理函数
    def capitalize_first_letter(text):
        """将文本的第一个字母转为大写"""
        if text and len(text) > 0:
            return text[0].upper() + text[1:]
        return text
    
    result2, process_info2 = smart_llm_call(
        text=test_text,
        block_prompt_template=block_prompt_template,
        merge_prompt_template=new_merge_template,
        system_message=system_message,
        post_process_fn=capitalize_first_letter,
        max_retries=1
    )
    
    print(f"\n测试2结果: {result2[:100]}...\n")
    print(f"处理过程中的步骤数: {len(process_info2)}")
    print(f"总Token使用量: {sum(item.get('tokens', 0) for item in process_info2)}")
    
    # 测试3：处理更长的文本，测试分块功能
    print("\n测试3: 处理更长的文本，测试分块功能...")
    
    # 创建一个更长的文本，重复测试文本10次，并使用更小的块大小
    long_text = test_text * 10 + """
    Additional information about Express Entry system:
    
    Express Entry is an application management system that Canada uses for three economic immigration programs: the Federal Skilled Worker Program, the Federal Skilled Trades Program, and the Canadian Experience Class.
    
    The system uses a points-based system called the Comprehensive Ranking System (CRS) to rank candidates. The CRS awards points for factors such as age, education, language skills, work experience, and adaptability.
    
    Regular draws are held where the highest-ranking candidates are invited to apply for permanent residence. These draws can be general, meaning they include candidates from all programs, or program-specific, focusing on one program or a specific category.
    
    Category-based selection was introduced in 2023 to help Canada address specific economic needs and labor shortages. Under this approach, IRCC can invite candidates based on their work experience in specific occupations or sectors, regardless of their CRS score.
    
    The Trade category is one of several categories created under this new approach. Others include healthcare, STEM professions, transport, agriculture and agri-food, and strong French language proficiency.
    
    Candidates who receive an ITA have 60 days to submit a complete application for permanent residence. Processing times for these applications can vary but typically range from 6 to 12 months.
    
    Once approved, candidates become permanent residents of Canada, which grants them most of the rights of Canadian citizens, except for the right to vote and run for political office.
    
    The history of Express Entry:
    
    Express Entry was launched in January 2015 as a replacement for the previous first-come, first-served application management system. The goal was to create a more efficient and flexible system that could respond to labor market needs.
    
    Initially, Express Entry was designed to prioritize candidates with job offers or provincial nominations. However, in November 2016, IRCC made significant changes to the CRS, reducing the points awarded for job offers and increasing the points for Canadian education.
    
    In June 2017, IRCC introduced additional points for candidates with strong French language skills and siblings in Canada.
    
    The COVID-19 pandemic led to further changes in 2020 and 2021, with IRCC focusing on candidates already in Canada through the Canadian Experience Class and Provincial Nominee Programs.
    
    In 2023, category-based selection was introduced as a new feature of Express Entry, allowing IRCC to target candidates with specific skills or attributes.
    
    The future of Express Entry:
    
    IRCC continues to refine and adapt Express Entry to meet Canada's evolving immigration needs. Future changes could include further modifications to the CRS, new categories for targeted draws, or integration with other immigration programs.
    
    The system is also expected to incorporate more digital tools and automation to improve efficiency and reduce processing times.
    
    As Canada seeks to address labor shortages and demographic challenges, Express Entry will remain a key pathway for skilled immigrants to obtain permanent residence.
    """ * 3  # 重复额外信息3次，确保文本足够长
    
    result3, process_info3 = smart_llm_call(
        text=long_text,
        block_prompt_template=block_prompt_template,
        merge_prompt_template=new_merge_template,
        system_message=system_message,
        post_process_fn=capitalize_first_letter,
        chunk_size=1000,  # 使用更小的块大小以确保文本被分块
        chunk_overlap=100,  # 减小重叠大小
        max_retries=1
    )
    
    print(f"\n测试3结果: {result3[:100]}...\n")
    print(f"处理过程中的步骤数: {len(process_info3)}")
    print(f"块数量: {len([p for p in process_info3 if p['step'].startswith('block_')])}")
    print(f"总Token使用量: {sum(item.get('tokens', 0) for item in process_info3)}")
    
    # 保存处理过程信息到文件
    with open("smart_llm_call_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "test1": {
                "result": result,
                "process": process_info
            },
            "test2": {
                "result": result2,
                "process": process_info2
            },
            "test3": {
                "result": result3,
                "process": process_info3
            }
        }, f, ensure_ascii=False, indent=2)
    
    print("\n测试结果已保存到 smart_llm_call_test_results.json")

if __name__ == "__main__":
    test_smart_llm_call() 