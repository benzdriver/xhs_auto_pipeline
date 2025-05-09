import json
import re

input_path = "data/generated_content.json"
output_path = "data/generated_content.html"

with open(input_path, "r") as f:
    data = json.load(f)

html = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>小红书风格内容预览</title>
<style>
body { background: #faf7f2; font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; }
.card { background: #fff; border-radius: 18px; box-shadow: 0 2px 8px #eee; margin: 32px auto; max-width: 600px; padding: 28px 28px 18px 28px; }
.title { color: #e9435a; font-size: 1.3em; font-weight: bold; margin-bottom: 10px; }
.meta { color: #888; font-size: 0.95em; margin-bottom: 8px; }
.content { font-size: 1.08em; margin-bottom: 12px; line-height: 1.7; }
.images { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
.images img { border-radius: 10px; max-width: 180px; max-height: 180px; object-fit: cover; }
.keywords { margin-bottom: 8px; }
.keyword { display: inline-block; background: #ffe6ea; color: #e9435a; border-radius: 12px; padding: 2px 12px; margin-right: 6px; font-size: 0.95em; }
a { color: #e9435a; text-decoration: none; }
a:hover { text-decoration: underline; }
</style>
</head>
<body>
<h1 style="text-align:center;color:#e9435a;">小红书风格内容预览</h1>
"""

for item in data:
    html += '<div class="card">'
    html += f'<div class="title">{item["title"]}</div>'
    html += f'<div class="meta">来源：{item["source"]} | 热度排名：{item["ranking"]} | <a href="{item["url"]}" target="_blank">原文链接</a></div>'
    # 分段处理
    content = item["content"]
    # 先按两个及以上换行分段
    paragraphs = re.split(r'\n{2,}', content)
    html += '<div class="content">'
    for para in paragraphs:
        para = para.strip().replace('\n', '<br>')  # 单个换行保留
        if para:
            html += f'<p>{para}</p>'
    html += '</div>'
    html += '</div>'

html += "</body></html>"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"已生成小红书风格 HTML 预览：{output_path}")
