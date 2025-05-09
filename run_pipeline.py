import sys
import json
from stages import fetch_trends, generate_content, generate_image, push_to_notion

STAGE = sys.argv[1] if len(sys.argv) > 1 else "all"

if STAGE == "fetch_trends" or STAGE == "all":
    print("==== [阶段1] 抓取 Google Trends 热词 ====")
    trend_data = fetch_trends.run()
    print(f"抓取到 {len(trend_data)} 条热词，已保存到 data/trends.json")
    with open("data/trends.json", "w") as f:
        json.dump(trend_data, f, ensure_ascii=False, indent=2)

if STAGE == "generate_content" or STAGE == "all":
    print("==== [阶段2] 生成内容 ====")
    trend_data = json.load(open("data/trends.json"))
    content_data = generate_content.run(trend_data)
    print(f"生成 {len(content_data)} 条内容，已保存到 data/content.json")
    with open("data/content.json", "w") as f:
        json.dump(content_data, f, ensure_ascii=False, indent=2)

if STAGE == "generate_image" or STAGE == "all":
    print("==== [阶段3] 生成图片并上传图床 ====")
    content_data = json.load(open("data/content.json"))
    image_data = generate_image.run(content_data)
    print(f"生成 {len(image_data)} 条图片内容，已保存到 data/image_content.json")
    with open("data/image_content.json", "w") as f:
        json.dump(image_data, f, ensure_ascii=False, indent=2)

if STAGE == "push_to_notion" or STAGE == "all":
    print("==== [阶段4] 推送到 Notion ====")
    image_data = json.load(open("data/image_content.json"))
    push_to_notion.run(image_data)
    print("已推送到 Notion 数据库")
