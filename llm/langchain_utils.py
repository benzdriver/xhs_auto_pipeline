"""
LangChain通用功能模块，提供基于LangChain的文本处理和内容生成功能。
可被其他模块调用，实现代码复用。
"""

import json
import os
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import openai
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# LangChain导入 - 使用最新的包结构
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnablePassthrough

from utils.load_config import load_all_config
from utils.logger import get_logger

# 加载配置
config = load_all_config()
openai.api_key = config["openai_api_key"]

# 枫人院风格定义 - 可在调用时覆盖
DEFAULT_STYLE = """
枫人院爆料风格特点：
1. 夸张化解读：用更有戏剧性的描述来解释政策变动
2. 信息+观点：给出客观事实，但加入独到的解读和分析
3. 情绪化表达：使用感叹号、反问句等增加情绪张力
4. 比喻和类比：将复杂政策用通俗比喻解释
5. 强调独家视角：突出"枫人院独家"等标签，强调信息渠道的独特性
"""

# 初始化日志
logger = get_logger("langchain_utils")

class ContentGenerator:
    """内容生成器类，使用LangChain处理文本并生成内容"""
    
    def __init__(self, model_name="gpt-4", temperature=0.8):
        """初始化内容生成器"""
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=config["openai_api_key"]
        )
        
        # 优化文本分割器配置
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=400,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
            is_separator_regex=False
        )
    
    def generate_fact_summary(self, text: str) -> str:
        """将长文本分块处理，生成事实摘要"""
        # 分割长文本
        chunks = self.text_splitter.split_text(text)
        
        # 如果只有一个块，直接处理
        if len(chunks) == 1:
            summary_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template(
                    """
                    请用简明扼要的中文，总结以下新闻原文中的关键事实、数据、政策变化、官方表述和细节：
                    
                    {text}
                    
                    总结:
                    """
                )
            ])
            
            # 使用最新的链式调用方式
            chain = summary_prompt | self.llm
            response = chain.invoke({"text": chunks[0]})
            return response.content
        
        # 多块处理
        # 1. 为每个块生成摘要
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template(
                    """
                    请用简明扼要的中文，总结以下新闻原文块中的关键事实、数据、政策变化、官方表述和细节：
                    
                    【文本块 {i}/{total}】
                    {chunk}
                    
                    【注意】仅总结这个块的关键信息，不要试图总结整篇文章。
                    
                    块摘要:
                    """
                )
            ])
            
            # 使用最新的链式调用方式
            chain = chunk_prompt | self.llm
            response = chain.invoke({"chunk": chunk, "i": i+1, "total": len(chunks)})
            chunk_summaries.append(response.content)
        
        # 2. 合并所有块摘要
        merge_prompt = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template(
                """
                请将以下多个文本块的摘要整合成一个连贯、完整的事实总结：
                
                {summaries}
                
                【要求】
                1. 消除重复信息
                2. 保持事实准确性
                3. 确保逻辑连贯性
                4. 返回一段完整的总结文字
                
                完整总结:
                """
            )
        ])
        
        # 格式化所有块摘要
        all_summaries = "\n\n".join(f"【块 {i+1} 摘要】\n{summary}" for i, summary in enumerate(chunk_summaries))
        
        # 使用最新的链式调用方式
        chain = merge_prompt | self.llm
        response = chain.invoke({"summaries": all_summaries})
        return response.content
    
    def generate_structured_content(self, fact_summary: str, output_structure: BaseModel, 
                               context: Dict[str, Any], style: str = DEFAULT_STYLE,
                               min_content_length: int = 500) -> BaseModel:
        """
        生成结构化内容
        
        Args:
            fact_summary: 事实摘要
            output_structure: 输出结构的Pydantic模型
            context: 上下文信息，如标题、来源等
            style: 生成风格指南
            min_content_length: 最小内容长度要求
            
        Returns:
            结构化的内容对象
        """
        # 初始化Pydantic输出解析器
        parser = PydanticOutputParser(pydantic_object=output_structure)
        
        # 创建包含格式指令的提示模板
        content_prompt = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template(
                """
                你是一位小红书爆款内容创作专家，请根据以下事实摘要，生成一篇关于加拿大移民的小红书爆款文案：
                
                【事实摘要】
                {fact_summary}
                
                【背景信息】
                {context}
                
                【写作风格】
                {style}
                
                【内容要求】
                1. 正文内容必须详细丰富，至少{min_length}字，包含多个段落
                2. 深度挖掘故事，加入实用的移民建议和行动指南
                3. 使用符合小红书平台的写作风格：夸张、情绪化、有画面感
                4. 添加1-2个假设性场景，帮助读者理解政策影响
                5. 结尾使用互动性的问句或号召性语言，鼓励评论和分享
                
                {format_instructions}
                
                请务必确保你的回答能被成功解析为上述格式，同时保证内容既丰富详实又符合小红书平台特点。
                """
            )
        ])
        
        # 创建生成内容的链
        chain = content_prompt | self.llm | parser
        
        try:
            # 使用invoke生成内容
            parsed_content = chain.invoke({
                "fact_summary": fact_summary, 
                "context": json.dumps(context, ensure_ascii=False, indent=2),
                "style": style,
                "min_length": min_content_length,
                "format_instructions": parser.get_format_instructions()
            })
            
            # 验证内容长度
            if hasattr(parsed_content, "content") and len(parsed_content.content) < min_content_length:
                # 如果内容太短，尝试重新生成更详细的内容
                print(f"生成的内容太短，只有{len(parsed_content.content)}字，尝试重新生成更详细的内容...")
                
                # 添加更强的长度指示
                detail_prompt = ChatPromptTemplate.from_messages([
                    HumanMessagePromptTemplate.from_template(
                        """
                        你生成的内容太短了，只有{current_length}字。请基于以下信息，重新创作一篇更加详细、内容更丰富的小红书文案：
                        
                        【事实摘要】
                        {fact_summary}
                        
                        【已生成的内容】
                        {previous_content}
                        
                        【要求】
                        1. 大幅扩展正文内容，至少{min_length}字，添加更多细节、例子和实用建议
                        2. 保持相同的标题和基本观点，但增加内容的深度和广度
                        3. 添加更多枫人院独家视角和爆料内容
                        4. 增加实用的移民建议和个人化的案例分析
                        5. 加强情感共鸣和读者互动的部分
                        
                        {format_instructions}
                        
                        请确保输出符合格式要求，并且内容丰富有深度。
                        """
                    )
                ])
                
                # 使用最新的链式调用方式
                detail_chain = detail_prompt | self.llm | parser
                
                # 重新生成更详细的内容
                parsed_content = detail_chain.invoke({
                    "fact_summary": fact_summary,
                    "previous_content": parsed_content.content,
                    "current_length": len(parsed_content.content),
                    "min_length": min_content_length,
                    "format_instructions": parser.get_format_instructions()
                })
            
            return parsed_content
            
        except OutputParserException as e:
            print(f"解析输出时发生错误: {e}")
            return None

def get_content_generator(model_name="gpt-4", temperature=0.8):
    """
    获取内容生成器
    
    Args:
        model_name (str): 使用的模型名称
        temperature (float): 温度参数，控制创意度
        
    Returns:
        function: 内容生成函数
    """
    logger.info(f"初始化内容生成器: 模型={model_name}, 温度={temperature}")
    
    # 创建LLM模型
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=temperature
    )
    
    # 创建内容生成器函数
    def generate_content(news_data, platform="小红书", channel="枫人院的放大镜"):
        """
        基于新闻内容生成小红书内容
        
        Args:
            news_data (dict): 新闻数据
            platform (str): 发布平台
            channel (str): 频道名称
            
        Returns:
            dict: 生成的内容
        """
        logger.debug(f"为平台 {platform} 的 {channel} 生成内容 (标题: {news_data.get('title', '无标题')})")
        
        # 这里只是基本实现，实际生产环境需要更复杂的提示和处理
        prompt_template = PromptTemplate(
            input_variables=["title", "content", "platform", "channel"],
            template="""
            你是一个专业的加拿大移民顾问，现在需要将以下新闻改写为适合{platform}平台"{channel}"账号的内容。
            
            新闻标题: {title}
            新闻内容: {content}
            
            请生成一个引人入胜的{platform}帖子，包括:
            1. 吸引人的标题 (25字以内)
            2. 内容摘要 (50字以内)
            3. 正文内容 (500-800字)
            4. 5个适合制作封面的关键词
            5. 2个问题来引发讨论
            
            以JSON格式返回，格式如下:
            {{
                "title": "标题",
                "headline": "摘要",
                "content": "正文内容",
                "image_keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
                "questions": ["问题1", "问题2"]
            }}
            """
        )
        
        # 创建LLM链
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        try:
            # 运行链
            result = chain.run(
                title=news_data.get("title", ""),
                content=news_data.get("content", "")[:2000],  # 限制内容长度
                platform=platform,
                channel=channel
            )
            
            # 解析结果
            try:
                # 尝试解析JSON
                parsed_result = json.loads(result)
                logger.info(f"内容生成成功: {parsed_result.get('title', '')}")
                return parsed_result
            except json.JSONDecodeError:
                logger.error(f"JSON解析失败: {result[:100]}...")
                # 尝试基本解析
                return {
                    "title": news_data.get("title", ""),
                    "headline": news_data.get("title", ""),
                    "content": result,
                    "image_keywords": [],
                    "questions": []
                }
                
        except Exception as e:
            logger.error(f"内容生成失败: {e}", exc_info=True)
            return {
                "title": news_data.get("title", ""),
                "headline": "内容生成失败",
                "content": "内容生成过程中发生错误，请稍后重试。",
                "image_keywords": [],
                "questions": []
            }
    
    return generate_content

def generate_fact_summary(text: str, model_name="gpt-4", temperature=0.8) -> str:
    """便捷函数：直接生成事实摘要"""
    generator = get_content_generator(model_name, temperature)
    return generator.generate_fact_summary(text)

def process_long_text(text: str, process_func, chunk_size=4000, chunk_overlap=400):
    """处理长文本的通用函数"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False
    )
    chunks = splitter.split_text(text)
    return process_func(chunks) 