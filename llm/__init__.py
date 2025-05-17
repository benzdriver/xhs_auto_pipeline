"""
llm包 - 提供大语言模型相关的功能

主要模块:
- call_gpt: 提供直接调用OpenAI API的功能
- langchain_utils: 提供基于LangChain的文本处理和内容生成功能
- models: 提供内容生成使用的数据模型定义
"""

# 从call_gpt导出核心函数
from llm.call_gpt import call_gpt, smart_llm_call

# 从langchain_utils导出核心功能
from llm.langchain_utils import (
    ContentGenerator,
    get_content_generator,
    generate_fact_summary,
    process_long_text
)

# 从models导出数据模型
from llm.models import XiaohongshuContent, WeiboContent, StructuredNewsAnalysis

# 版本信息
__version__ = "0.1.0"

# llm 模块初始化文件
# 使包能够被导入 