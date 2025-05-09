import openai
from utils.load_config import load_all_config
from langchain.text_splitter import TokenTextSplitter

config = load_all_config()
client = openai.OpenAI(api_key=config["openai_api_key"])

def call_gpt(prompt, model="gpt-4", temperature=0.7):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def smart_llm_call(
    text,
    block_prompt_template,
    merge_prompt_template,
    model="gpt-4",
    chunk_size=3000,
    chunk_overlap=200,
    encoding_name="cl100k_base",
    temperature=0.7
):
    """
    智能分段调用 LLM，返回最终结果和所有 prompt/response 追踪信息。
    - text: 原始长文本
    - block_prompt_template: 用于每块的 prompt，支持 {block}、{idx}、{total}
    - merge_prompt_template: 合并所有分块摘要的 prompt，支持 {fact_summary}
    """
    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, encoding_name=encoding_name)
    prompts_and_responses = []
    if len(text) > chunk_size:
        blocks = splitter.split_text(text)
        block_summaries = []
        for idx, block in enumerate(blocks):
            block_prompt = block_prompt_template.format(block=block, idx=idx+1, total=len(blocks))
            summary = call_gpt(block_prompt, model=model, temperature=temperature)
            prompts_and_responses.append({"step": f"block_{idx+1}", "prompt": block_prompt, "response": summary})
            block_summaries.append(summary)
        fact_summary = ""
        for i, summary in enumerate(block_summaries):
            fact_summary += f"【分块{i+1}摘要】\n{summary}\n"
        merge_prompt = merge_prompt_template.format(fact_summary=fact_summary)
        final_result = call_gpt(merge_prompt, model=model, temperature=temperature)
        prompts_and_responses.append({"step": "merge", "prompt": merge_prompt, "response": final_result})
        return final_result, prompts_and_responses
    else:
        block_prompt = block_prompt_template.format(block=text, idx=1, total=1)
        result = call_gpt(block_prompt, model=model, temperature=temperature)
        prompts_and_responses.append({"step": "single_block", "prompt": block_prompt, "response": result})
        return result, prompts_and_responses
