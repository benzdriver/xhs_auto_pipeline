# XHS Auto Pipeline

自动化加拿大移民内容生成与发布系统，用于抓取热门话题、生成相关移民内容、配图，并发布到Notion平台。

## 功能概述

该项目实现了一个完整的自动化内容生成管道，包含以下功能：

1. **趋势抓取**：使用Google Trends抓取加拿大移民相关的热门话题和关键词，并抓取相关新闻文章
2. **内容生成**：利用AI分析新闻内容，生成针对"枫人院的放大镜"频道的专业移民内容
3. **图像生成**：使用DALL-E 3生成高质量的小红书风格配图，并自动上传到Imgur图床
4. **Notion发布**：自动将生成的内容和图片发布到Notion数据库
5. **集中式日志**：详细记录每个阶段的执行情况，支持日志分析和错误排查

## 项目结构

```
xhs_auto_pipeline/
├── .env               # 环境变量配置文件（API密钥等）
├── constants.py       # 常量定义
├── requirements.txt   # 依赖项
├── run_pipeline.py    # 主执行脚本
├── run_workflow.py    # 工作流执行脚本（带日志和错误处理）
├── ENV_SETUP.md       # 环境变量设置指南
├── data/              # 数据存储目录
├── docs/              # 文档目录
│   └── LOGGING.md     # 日志系统使用指南
├── llm/               # LLM调用模块
│   ├── langchain_utils.py  # LangChain工具函数
│   └── models.py           # Pydantic模型定义
├── stages/            # 处理流程各阶段
│   ├── fetch_trends.py         # 抓取趋势和新闻
│   ├── generate_content_langchain.py  # 使用LangChain生成内容
│   ├── generate_image.py       # 生成图片并上传到Imgur
│   ├── upload_to_imgur.py      # 图片上传到Imgur
│   └── push_to_notion.py       # 推送到Notion
├── utils/             # 实用工具函数
│   ├── load_config.py   # 配置加载
│   ├── cache_utils.py   # 缓存管理
│   ├── logger.py        # 日志系统
│   ├── log_analyzer.py  # 日志分析工具
│   └── ...
└── logs/              # 日志存储目录
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

3. 配置环境变量：
   - 在项目根目录创建`.env`文件
   - 设置必要的API密钥和配置
   - 详细说明请参考 [ENV_SETUP.md](ENV_SETUP.md)

## 使用方法

### 运行完整工作流

使用工作流脚本运行（带错误处理和日志）：
```bash
python run_workflow.py
```

### 运行特定阶段

使用pipeline脚本运行特定阶段：
```bash
python run_pipeline.py fetch_trends      # 只运行趋势抓取
python run_pipeline.py generate_content  # 只运行内容生成
python run_pipeline.py generate_image    # 只运行图片生成
python run_pipeline.py push_to_notion    # 只运行Notion推送
```

### 重置特定阶段处理状态

如果需要重新处理某个阶段的数据：
```bash
python run_pipeline.py reset fetch_trends      # 重置趋势抓取状态
python run_pipeline.py reset generate_content  # 重置内容生成状态
python run_pipeline.py reset generate_image    # 重置图片生成状态
```

### 分析日志和工作流执行情况

使用日志分析工具查看执行情况和错误：
```bash
python utils/log_analyzer.py             # 分析所有日志和工作流
python utils/log_analyzer.py --workflow  # 只分析工作流执行情况
python utils/log_analyzer.py --file workflow.log  # 分析特定日志文件
python utils/log_analyzer.py --all --verbose      # 分析所有日志并显示详细信息
```

## 日志系统

该项目实现了一个集中式日志系统，支持以下功能：

1. **分阶段日志**：每个处理阶段都有独立的日志文件，方便定位问题
2. **多级日志**：支持DEBUG、INFO、WARNING、ERROR等不同级别的日志
3. **双重输出**：同时输出到控制台和日志文件，方便实时查看和后期分析
4. **日志分析工具**：内置日志分析功能，快速获取执行情况和错误统计

详细的日志系统使用说明请参考 [docs/LOGGING.md](docs/LOGGING.md)。

## 图片生成功能

新增的DALL-E图片生成功能具有以下特点：

1. **智能提示生成**：根据内容标题、副标题和关键词自动生成DALL-E提示
2. **加拿大元素融合**：图片中自动融入加拿大元素（如枫叶、国旗等）
3. **小红书风格**：生成符合小红书平台审美的现代、时尚风格图片
4. **Imgur集成**：自动将生成的图片上传到Imgur图床，便于Notion展示
5. **缓存管理**：避免重复处理，节省API调用

## 依赖项

* openai: AI内容和图片生成
* langchain: 高级LLM工作流管理
* notion-client: Notion API交互
* pytrends: Google趋势分析
* requests: HTTP请求和Imgur上传
* python-dotenv: 环境变量管理
* beautifulsoup4: 网页内容解析

## 环境变量

所有配置都通过环境变量管理，包括API密钥、模型选择等。详细的环境变量设置说明请参考 [ENV_SETUP.md](ENV_SETUP.md)。

## 注意事项

* 所有API密钥和配置项都存储在`.env`文件中，该文件已加入`.gitignore`避免提交敏感信息
* 数据文件存储在data/目录，也已加入`.gitignore`
* 运行pipeline前请确保网络连接畅通，并有足够的API调用额度
* 图片生成会消耗OpenAI API额度，请注意控制使用频率

## 许可证

查看 [LICENSE](LICENSE) 文件了解详情。

## Google Trends 数据获取

本项目使用多种方法获取 Google Trends 数据，按照优先级顺序：

1. **SerpAPI** (推荐): 通过 SerpAPI 服务获取趋势数据，能够有效绕过 Google 的反爬虫措施
2. **PyTrends**: 如果 SerpAPI 不可用，则使用 PyTrends 库直接获取数据
3. **智能后备**: 当以上方法都失败时，使用预定义的规则和分数估算热度

### 配置 SerpAPI

要使用 SerpAPI 获取 Google Trends 数据：

1. 获取 SerpAPI 密钥：访问 [SerpAPI](https://serpapi.com/) 注册账号并获取 API 密钥
2. 设置环境变量：
   ```bash
   export SERPAPI_KEY=your_api_key_here
   export USE_SERPAPI=true
   ```
3. 或者在 `.env` 文件中添加：
   ```
   SERPAPI_KEY=your_api_key_here
   USE_SERPAPI=true
   ```

### 测试趋势数据获取

使用以下命令测试 Google Trends 数据获取功能：

```bash
python test_serpapi.py
```

该脚本会测试:
- 批量处理方法 (按优先级使用 SerpAPI 和 PyTrends)
- 直接使用 SerpAPI (如果配置了密钥)
- 直接使用 PyTrends

测试结果将保存在 `test_results/trends_method_comparison.json` 文件中。