import requests
import json
import time

CANVA_API_KEY = "your_canva_api_key"
TEMPLATE_ID = "your_template_id"
API_URL = f"https://api.canva.com/v1/designs/{TEMPLATE_ID}/render"

def generate_canva_poster(title, headline, content, output_path):
    payload = {
        "elements": {
            "title": title,
            "headline": headline,
            "content": content
        }
    }
    headers = {
        "Authorization": f"Bearer {CANVA_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    image_url = resp.json()["image_url"]
    # 下载图片
    img_data = requests.get(image_url).content
    with open(output_path, "wb") as f:
        f.write(img_data)
    return output_path

def batch_generate_posters(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    for idx, item in enumerate(data):
        title = item.get("title", "")
        headline = item.get("headline", "")
        content = item.get("content", "")
        output_path = f"data/poster_{idx+1}.png"
        print(f"正在生成第{idx+1}张海报...")
        try:
            generate_canva_poster(title, headline, content, output_path)
            print(f"已保存：{output_path}")
        except Exception as e:
            print(f"生成失败：{e}")
        time.sleep(1)  # 防止 API 速率限制

if __name__ == "__main__":
    batch_generate_posters("data/generated_content.json")
