# 环境变量设置指南

本项目使用环境变量来管理API密钥和配置。请按照以下步骤设置您的环境变量。

## 创建 .env 文件

在项目根目录下创建一个名为 `.env` 的文件，并添加以下内容：

```
# OpenAI配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
DALLE_MODEL=dall-e-3

# Notion配置
NOTION_API_KEY=your-notion-secret-api-key
NOTION_DATABASE_ID=your-notion-database-id

# 地区和关键词配置
GEO=CA
TRENDING_KEYWORDS=Canada immigration,Express Entry,PR card,PNP,Study permit

# Imgur配置
IMGUR_CLIENT_ID=your-imgur-client-id
IMGUR_CLIENT_SECRET=your-imgur-client-secret

# 代理配置
USE_PROXY=false
PROXY_ROTATION_INTERVAL=300
SMARTPROXY_USERNAME=your-smartproxy-username
SMARTPROXY_PASSWORD=your-smartproxy-password
SMARTPROXY_ENDPOINT=gate.smartproxy.com
SMARTPROXY_PORT=7000
SMARTPROXY_ADDITIONAL_PORTS=8000,9000
CUSTOM_PROXIES=[{"server":"http://proxy1.example.com:8080","username":"user1","password":"pass1"}]

# 验证码服务配置
CAPTCHA_SERVICE=2captcha
TWOCAPTCHA_API_KEY=your-2captcha-api-key

# 趋势配置
MAX_REQUESTS_PER_IP=10
IP_COOLDOWN_MINUTES=60
TIMEFRAME=now 7-d
USE_SERPAPI=false
SERPAPI_KEY=your-serpapi-api-key
```

## 配置说明

### OpenAI 配置

- `OPENAI_API_KEY`: 您的OpenAI API密钥，可从 [OpenAI平台](https://platform.openai.com/account/api-keys) 获取
- `OPENAI_MODEL`: 使用的OpenAI模型，推荐使用 "gpt-4" 或 "gpt-3.5-turbo"
- `DALLE_MODEL`: 使用的DALL-E模型，推荐使用 "dall-e-3"

### Notion 配置

- `NOTION_API_KEY`: 您的Notion API密钥，可从 [Notion开发者页面](https://www.notion.so/my-integrations) 获取
- `NOTION_DATABASE_ID`: 您的Notion数据库ID，可从数据库URL中获取
  - 例如: `https://www.notion.so/myworkspace/a8aec43384f447ed84390e8e42c2e089?v=...`
  - 其中 `a8aec43384f447ed84390e8e42c2e089` 就是数据库ID

### 地区和关键词配置

- `GEO`: 地理位置代码，用于Google Trends查询，默认为"CA"（加拿大）
- `TRENDING_KEYWORDS`: 默认关键词列表，用逗号分隔

### Imgur 配置

- `IMGUR_CLIENT_ID`: Imgur客户端ID，可从 [Imgur开发者页面](https://api.imgur.com/oauth2/addclient) 获取
- `IMGUR_CLIENT_SECRET`: Imgur客户端密钥

### 代理配置

- `USE_PROXY`: 是否启用代理功能，设置为 "true" 或 "false"
- `PROXY_ROTATION_INTERVAL`: 代理轮换间隔（秒）
- `SMARTPROXY_USERNAME`: SmartProxy用户名
- `SMARTPROXY_PASSWORD`: SmartProxy密码
- `SMARTPROXY_ENDPOINT`: SmartProxy服务器地址
- `SMARTPROXY_PORT`: SmartProxy端口
- `SMARTPROXY_ADDITIONAL_PORTS`: 额外的SmartProxy端口，用逗号分隔
- `CUSTOM_PROXIES`: 自定义代理列表，JSON格式的数组

### 验证码服务配置

- `CAPTCHA_SERVICE`: 验证码解决服务，目前支持 "2captcha"
- `TWOCAPTCHA_API_KEY`: 2Captcha服务的API密钥

### 趋势配置

- `MAX_REQUESTS_PER_IP`: 每个IP的最大请求数
- `IP_COOLDOWN_MINUTES`: IP冷却时间（分钟）
- `TIMEFRAME`: Google Trends时间范围，默认为 "now 7-d"
- `USE_SERPAPI`: 是否使用SerpAPI获取Google Trends数据，设置为 "true" 启用
- `SERPAPI_KEY`: SerpAPI的API密钥，从 [SerpAPI](https://serpapi.com/) 获取

## 注意事项

- `.env` 文件包含敏感信息，已被添加到 `.gitignore` 中，不会被提交到Git仓库
- 确保您的API密钥有足够的权限和额度
- 如果您在部署到服务器，可以直接在服务器环境中设置这些环境变量，而不是使用 `.env` 文件 