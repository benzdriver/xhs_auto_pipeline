# XHS Auto Pipeline

自动化加拿大移民内容生成与发布系统，用于抓取热门话题、生成相关移民内容、配图，并发布到Notion平台。

## 功能概述

该项目实现了一个完整的自动化内容生成管道，包含以下功能：

1. **趋势抓取**：使用Google Trends抓取加拿大移民相关的热门话题和关键词，并抓取相关新闻文章
2. **内容生成**：利用AI分析新闻内容，生成针对"枫人院的放大镜"频道的专业移民内容
3. **图像生成**：基于内容关键词生成相关配图
4. **Notion发布**：自动将生成的内容和图片发布到Notion数据库

## 项目结构

```
xhs_auto_pipeline/
├── config.json          # 配置文件（API密钥等）
├── constants.py         # 常量定义
├── requirements.txt     # 依赖项
├── run_pipeline.py      # 主执行脚本
├── data/                # 数据存储目录
├── llm/                 # LLM调用模块
├── stages/              # 处理流程各阶段
│   ├── fetch_trends.py      # 抓取趋势和新闻
│   ├── generate_content.py  # 生成内容
│   ├── generate_image.py    # 生成图片
│   ├── push_to_notion.py    # 推送到Notion
│   └── ...
├── utils/               # 实用工具函数
└── fonts/               # 图像生成使用的字体
```

## 安装指南

1. 克隆仓库：
```bash
git clone https://github.com/username/xhs_auto_pipeline.git
cd xhs_auto_pipeline
```

2. 创建虚拟环境并安装依赖：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. 配置API密钥：
   - 复制`config.json.example`为`config.json`（如果存在）
   - 填入所需的API密钥（OpenAI、Notion等）

## 使用方法

运行完整流程：
```bash
python run_pipeline.py
```

运行特定阶段：
```bash
python run_pipeline.py fetch_trends      # 只运行趋势抓取
python run_pipeline.py generate_content  # 只运行内容生成
python run_pipeline.py generate_image    # 只运行图片生成
python run_pipeline.py push_to_notion    # 只运行Notion推送
```

## 依赖项

* openai: AI内容生成
* notion-client: Notion API交互
* google-api-python-client: Google API交互
* requests: HTTP请求
* pytrends: Google趋势分析

## 注意事项

* 代码中的配置项和API密钥需要在config.json中设置
* 数据文件存储在data/目录，已加入.gitignore避免提交敏感信息
* 运行pipeline前请确保网络连接畅通，并有足够的API调用额度

## 许可证

查看 [LICENSE](LICENSE) 文件了解详情。