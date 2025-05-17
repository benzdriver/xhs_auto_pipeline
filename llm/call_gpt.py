import openai
import tiktoken
from typing import List, Dict, Any, Tuple, Optional, Callable
from utils.load_config import load_all_config
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

config = load_all_config()
client = openai.OpenAI(api_key=config["openai_api_key"])

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def call_gpt(prompt, model="gpt-4", temperature=0.7, system_message=None):
    messages = []
    
    # 如果提供了系统消息，添加到消息列表
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    # 添加用户消息
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API 调用失败: {e}")
        raise

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """计算文本的token数量"""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

def smart_llm_call(
    text: str,
    block_prompt_template: str,
    merge_prompt_template: str,
    model: str = "gpt-4",
    chunk_size: int = 4000,
    chunk_overlap: int = 400,
    temperature: float = 0.7,
    system_message: Optional[str] = None,
    max_retries: int = 2,
    post_process_fn: Optional[Callable[[str], str]] = None,
    encoding_name: str = "cl100k_base"  # 为了与旧版兼容保留此参数
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    增强版智能分段调用 LLM，返回最终结果和所有 prompt/response 追踪信息。
    
    Args:
        text: 原始长文本
        block_prompt_template: 用于每块的提示模板，支持 {block}、{idx}、{total}
        merge_prompt_template: 合并所有分块摘要的提示模板，支持 {summaries} 或 {fact_summary}
        model: 使用的OpenAI模型名称
        chunk_size: 分块大小（以token计）
        chunk_overlap: 分块重叠大小（以token计）
        temperature: 模型温度参数
        system_message: 可选的系统消息
        max_retries: API调用失败时的最大重试次数
        post_process_fn: 对每个块处理结果的后处理函数
        encoding_name: 编码名称（为了与旧版兼容保留此参数）
        
    Returns:
        Tuple[str, List[Dict[str, Any]]]: (最终结果, 处理过程的跟踪信息)
    """
    # 使用更先进的RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    prompts_and_responses = []
    
    try:
        # 计算原始文本的大致token数
        estimated_tokens = count_tokens(text)
        logger.info(f"原始文本长度约 {estimated_tokens} tokens")
        
        # 如果文本足够短，可以直接处理
        if estimated_tokens <= chunk_size:
            logger.info("文本较短，直接处理")
            block_prompt = block_prompt_template.format(block=text, idx=1, total=1)
            
            # 带重试的API调用
            result = None
            for attempt in range(max_retries + 1):
                try:
                    result = call_gpt(block_prompt, model=model, temperature=temperature, system_message=system_message)
                    break
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"API调用失败，第{attempt+1}次重试: {e}")
                    else:
                        logger.error(f"所有重试都失败: {e}")
                        raise
            
            # 应用后处理函数
            if post_process_fn and result:
                result = post_process_fn(result)
                
            prompts_and_responses.append({
                "step": "single_block", 
                "prompt": block_prompt, 
                "response": result,
                "tokens": count_tokens(block_prompt) + (count_tokens(result) if result else 0)
            })
            return result, prompts_and_responses
        
        # 对长文本进行分块处理
        logger.info(f"文本较长，进行分块处理")
        blocks = splitter.split_text(text)
        logger.info(f"文本被分为 {len(blocks)} 块")
        
        # 处理每个块
        block_summaries = []
        for idx, block in enumerate(blocks):
            block_prompt = block_prompt_template.format(block=block, idx=idx+1, total=len(blocks))
            
            # 带重试的API调用
            summary = None
            for attempt in range(max_retries + 1):
                try:
                    summary = call_gpt(
                        block_prompt, 
                        model=model, 
                        temperature=temperature,
                        system_message=system_message
                    )
                    break
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"块 {idx+1} API调用失败，第{attempt+1}次重试: {e}")
                    else:
                        logger.error(f"块 {idx+1} 所有重试都失败: {e}")
                        raise
            
            # 应用后处理函数
            if post_process_fn and summary:
                summary = post_process_fn(summary)
                
            prompts_and_responses.append({
                "step": f"block_{idx+1}", 
                "prompt": block_prompt, 
                "response": summary,
                "tokens": count_tokens(block_prompt) + (count_tokens(summary) if summary else 0)
            })
            block_summaries.append(summary)
        
        # 准备合并所有块摘要
        all_summaries = ""
        for i, summary in enumerate(block_summaries):
            all_summaries += f"【块 {i+1} 摘要】\n{summary}\n\n"
        
        # 检查模板中使用的是 {summaries} 还是 {fact_summary}
        if "{summaries}" in merge_prompt_template:
            merge_prompt = merge_prompt_template.format(summaries=all_summaries)
        elif "{fact_summary}" in merge_prompt_template:
            # 向后兼容：支持旧版本中使用的 {fact_summary}
            merge_prompt = merge_prompt_template.format(fact_summary=all_summaries)
        else:
            # 如果模板中既没有 {summaries} 也没有 {fact_summary}
            logger.warning("合并提示模板中没有找到 {summaries} 或 {fact_summary} 占位符，尝试直接使用模板")
            merge_prompt = merge_prompt_template
        
        # 带重试的API调用
        final_result = None
        for attempt in range(max_retries + 1):
            try:
                final_result = call_gpt(
                    merge_prompt, 
                    model=model, 
                    temperature=temperature,
                    system_message=system_message
                )
                break
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"合并步骤API调用失败，第{attempt+1}次重试: {e}")
                else:
                    logger.error(f"合并步骤所有重试都失败: {e}")
                    raise
        
        # 应用后处理函数
        if post_process_fn and final_result:
            final_result = post_process_fn(final_result)
            
        prompts_and_responses.append({
            "step": "merge", 
            "prompt": merge_prompt, 
            "response": final_result,
            "tokens": count_tokens(merge_prompt) + (count_tokens(final_result) if final_result else 0)
        })
        
        # 计算总token使用量
        total_tokens = sum(item.get("tokens", 0) for item in prompts_and_responses)
        logger.info(f"处理完成，总共使用约 {total_tokens} tokens")
        
        return final_result, prompts_and_responses
        
    except Exception as e:
        logger.error(f"smart_llm_call处理失败: {e}")
        # 即使失败，也尝试返回已收集的数据
        return f"处理失败: {str(e)}", prompts_and_responses
