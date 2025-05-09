import json
import requests
from utils.load_config import load_all_config

def upload_to_imgur(image_path, client_id):
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {client_id}"}
    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()["data"]["link"]
    else:
        print("Imgur 上传失败:", response.text)
        return None

if __name__ == "__main__":
    config = load_all_config()
    client_id = config["imgur_client_id"]

    with open("data/image_content.json", "r") as f:
        data = json.load(f)

    for item in data:
        local_path = item.get("final_image_path")
        if local_path and not item.get("imgur_url"):
            imgur_url = upload_to_imgur(local_path, client_id)
            item["imgur_url"] = imgur_url

    with open("data/image_content.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("所有图片已上传到 Imgur，并已更新 image_content.json。")
