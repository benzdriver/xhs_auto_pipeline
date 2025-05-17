# Google Trends 反爬虫措施

本文档介绍了针对 Google Trends 的反爬虫措施以及我们如何应对这些挑战。

## 检测到的问题

我们在提取 Google Trends 数据时发现了以下问题：

1. Google 实现了机器人验证 (CAPTCHA/reCAPTCHA) 检测
2. 持续请求会导致 429 (Too Many Requests) 错误
3. DOM 结构可能已更改，使得常规提取方法失效
4. 多个提取方法都无法从页面获取热度值

## 实施的解决方案

我们在 `fetch_trends.py` 实现了以下反爬虫策略：

### 1. 机器人验证检测与解决

- 添加了关键词检测以识别机器人验证页面
- 保存验证页面截图以便进一步分析
- 集成2Captcha服务自动解决验证码
- 在检测到验证页面时优雅降级到预定义分数

```python
robot_keywords = ["i'm not a robot", "captcha", "verify you're human", "robot verification", 
                  "are you a robot", "human verification", "我不是机器人", "人机验证"]
is_robot_check = any(kw.lower() in page_content for kw in robot_keywords)
```

### 2. 随机化和指纹隐藏

- 随机视口大小 (1280-1920 × 720-1080)
- 随机用户代理字符串
- 修改 Navigator 属性以隐藏自动化特征
- 随机硬件配置属性 (hardwareConcurrency, deviceMemory)
- 模拟常见浏览器插件

### 3. 模拟真实用户行为

- 在访问目标页面前先访问 Google 首页
- 随机鼠标移动和页面交互
- 偶尔在搜索框输入并删除文本
- 多次随机页面滚动，模拟阅读行为
- 增加页面等待时间 (5-10秒)
- 随机点击图表区域

### 4. 会话持久化

- 使用持久化浏览器数据目录保存 cookies 和会话数据
- 基于 tempfile 模块使用临时目录
- 这有助于重用已验证的会话

### 5. 代理支持

- 添加了代理配置支持
- 通过环境变量或配置文件控制代理设置
- 集成SmartProxy服务
- 支持自定义代理列表
- 实现代理轮换和黑名单机制

## 使用方法

### 环境变量配置 (.env文件)

现在我们已经集成了`.env`文件配置支持，您可以在项目根目录创建一个`.env`文件，包含以下配置：

```bash
# 代理配置
USE_PROXY=true
PROXY_ROTATION_INTERVAL=300
SMARTPROXY_USERNAME=your_smartproxy_username
SMARTPROXY_PASSWORD=your_smartproxy_password
SMARTPROXY_ENDPOINT=gate.smartproxy.com
SMARTPROXY_PORT=7000
SMARTPROXY_ADDITIONAL_PORTS=8000,9000

# 自定义代理列表 (JSON格式)
CUSTOM_PROXIES=[{"server":"http://proxy1.example.com:8080","username":"user1","password":"pass1"}]

# 验证码服务配置
CAPTCHA_SERVICE=2captcha
TWOCAPTCHA_API_KEY=your_2captcha_api_key

# 趋势配置
GEO=CA
TIMEFRAME=now 7-d
MAX_REQUESTS_PER_IP=10
IP_COOLDOWN_MINUTES=60
```

### SmartProxy设置

1. 注册[SmartProxy](https://smartproxy.com/)账户
2. 获取访问凭据
3. 在`.env`文件中设置凭据

### 2Captcha设置

1. 注册[2Captcha](https://2captcha.com/)账户
2. 充值账户余额
3. 获取API密钥
4. 在`.env`文件中设置API密钥

## 后续改进方向

1. 实现多IP轮换策略（已基本实现）
2. 与验证码解决服务集成（已基本实现）
3. 添加更多特征随机化
4. 实现更智能的请求频率限制
5. 实现机器学习模型直接从图表图像估算热度值
6. 添加对Anti-Captcha等其他验证码解决服务的支持 