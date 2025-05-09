import openai
import os
import requests
from utils.load_config import load_all_config
from PIL import Image, ImageDraw, ImageFont
from llm.call_gpt import call_gpt

config = load_all_config()

# 新版 openai>=1.0.0 客户端
client = openai.OpenAI(api_key=config["openai_api_key"])

FONTS = {
    "title": "fonts/AlibabaPuHuiTi-3-85-Bold/AlibabaPuHuiTi-3-85-Bold.ttf",
    "headline": "fonts/AlibabaPuHuiTi-3-55-Regular/AlibabaPuHuiTi-3-55-Regular.ttf",
    "fallback": "fonts/AlibabaPuHuiTi-3-55-Regular/AlibabaPuHuiTi-3-55-Regular.ttf"
}

def call_gpt_for_image_prompt(content, image_keywords=None):
    prompt = f"""
你是疯人院的爆料记者，请为以下小红书文案生成一段适合AI绘图的图片描述，要求：
- 画面要与文案内容相匹配，不要偏离文案内容
- 画面不要有文字
- 画面尽量跟真人照片类似
- 结合文案中的关键词和独家推理
- 适合小红书配图
【文案内容】
{content}
"""
    if image_keywords:
        prompt += f"\n【关键词】{', '.join(image_keywords)}"
    prompt += "\n【图片描述】"
    return call_gpt(prompt)

def call_dalle(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    return response.data[0].url

def download_image(image_url, save_dir, filename):
    os.makedirs(save_dir, exist_ok=True)
    response = requests.get(image_url)
    if response.status_code == 200:
        file_path = os.path.join(save_dir, filename)
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    else:
        print(f"下载失败: {image_url}")
        return None

def upload_to_imgur(image_path, client_id):
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {client_id}"}
    print(f"[DEBUG] 上传图片到 Imgur: {image_path}")
    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(url, headers=headers, files=files)
    print(f"[DEBUG] Imgur 响应状态码: {response.status_code}")
    try:
        print(f"[DEBUG] Imgur 响应内容: {response.text[:200]}")
    except Exception:
        pass
    if response.status_code == 200:
        data = response.json()["data"]
        return data["link"], data.get("deletehash")
    else:
        print("Imgur 上传失败:", response.text)
        return None, None

def delete_imgur_image(deletehash, client_id):
    url = f"https://api.imgur.com/3/image/{deletehash}"
    headers = {"Authorization": f"Client-ID {client_id}"}
    response = requests.delete(url, headers=headers)
    return response.status_code == 200

# 批量清理
def batch_delete_imgur_images(deletehash_list, client_id):
    for deletehash in deletehash_list:
        success = delete_imgur_image(deletehash, client_id)
        print(f"Delete {deletehash}: {'Success' if success else 'Failed'}")

def batch_delete_imgur_images_from_json(json_path, client_id):
    import json
    with open(json_path, "r") as f:
        data = json.load(f)
    for item in data:
        deletehash = item.get("imgur_deletehash")
        if deletehash:
            success = delete_imgur_image(deletehash, client_id)
            print(f"Delete {deletehash}: {'Success' if success else 'Failed'}")

def run(content_data):
    results = []
    client_id = config["imgur_client_id"]
    for idx, item in enumerate(content_data):
        # 确保 types 字段存在
        if "types" not in item or not item["types"]:
            item["types"] = [item.get("platform", "小红书")]
        # 1. 让 LLM 生成图片描述
        image_prompt = call_gpt_for_image_prompt(item["content"], item.get("image_keywords"))
        # 2. 用 DALL·E 生成图片
        image_url = call_dalle(image_prompt)
        # 3. 下载图片到本地
        base_img_path = download_image(image_url, "data/images", f"base_image_{idx+1}.png")
        # 4. 上传到 Imgur
        imgur_url, deletehash = upload_to_imgur(base_img_path, client_id) if base_img_path else (None, None)
        # 5. 写入 imgur_url 和 deletehash 字段
        item["imgur_url"] = imgur_url
        item["imgur_deletehash"] = deletehash
        results.append(item)
    return results

if __name__ == "__main__":
    import json
    input_path = "data/generated_content.json"
    output_path = "data/image_content.json"
    if not os.path.exists(input_path):
        print(f"[ERROR] {input_path} 不存在，请先运行 generate_content.py。")
    else:
        with open(input_path, "r") as f:
            content_data = json.load(f)
        results = run(content_data)
        with open(output_path, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 已生成图片并保存到 {output_path}，图片文件在 data/images/ 目录。")