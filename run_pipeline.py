import sys
import json
from stages import fetch_trends, generate_content, generate_image, push_to_notion
from utils.cache_utils import reset_stage_processing

# 检查是否请求重置某个阶段
if len(sys.argv) > 2 and sys.argv[1] == "reset":
    stage_to_reset = sys.argv[2]
    print(f"==== 重置阶段: {stage_to_reset} ====")
    reset_stage_processing(stage_to_reset)
    print(f"阶段 {stage_to_reset} 的处理状态已重置，下次运行将重新处理所有新闻")
    sys.exit(0)

STAGE = sys.argv[1] if len(sys.argv) > 1 else "all"

# 检查是否使用--force参数强制重新处理
force = "--force" in sys.argv
if force and STAGE != "all":
    print(f"==== 强制重新处理阶段: {STAGE} ====")
    reset_stage_processing(STAGE)

if STAGE == "fetch_trends" or STAGE == "all":
    print("==== [阶段1] 抓取 Google Trends 热词 ====")
    trend_data = fetch_trends.run()
    print(f"抓取到 {len(trend_data)} 条热词，已保存到 data/trends.json")
    with open("data/trends.json", "w") as f:
        json.dump(trend_data, f, ensure_ascii=False, indent=2)

if STAGE == "generate_content" or STAGE == "all":
    print("==== [阶段2] 生成内容 ====")
    content_data = generate_content.run(save_to_json=True)
    print(f"生成 {len(content_data)} 条内容，已保存到 data/generated_content.json")
    with open("data/generated_content.json", "w") as f:
        json.dump(content_data, f, ensure_ascii=False, indent=2)

if STAGE == "generate_image" or STAGE == "all":
    print("==== [阶段3] 生成图片并上传图床 ====")
    image_data = generate_image.run()
    print(f"生成 {len(image_data)} 条图片内容，已保存到 data/image_content.json")
    with open("data/image_content.json", "w") as f:
        json.dump(image_data, f, ensure_ascii=False, indent=2)

if STAGE == "push_to_notion" or STAGE == "all":
    print("==== [阶段4] 推送到 Notion ====")
    image_data = json.load(open("data/image_content.json"))
    push_to_notion.run(image_data)
    print("已推送到 Notion 数据库")
