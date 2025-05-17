# 日志系统使用指南

小红书内容生成工作流现在使用了一个集中式的日志系统，用于记录执行过程中的关键信息、警告和错误。这个系统可以同时将日志输出到控制台和特定的日志文件中，便于调试和查看执行历史。

## 日志系统特点

- **统一格式**: 所有日志条目都包含时间戳、日志级别、模块名称和消息内容
- **按阶段分离**: 每个工作流阶段都有自己的日志文件，便于查看特定阶段的执行情况
- **双重输出**: 同时输出到控制台和日志文件，方便实时监控和事后分析
- **不同级别**: 支持DEBUG、INFO、WARNING、ERROR等不同级别的日志，便于筛选重要信息

## 如何使用日志系统

### 1. 在模块中初始化日志记录器

```python
from utils.logger import get_logger

# 初始化日志记录器，参数为当前模块/阶段的名称
logger = get_logger("module_name")
```

### 2. 记录不同级别的日志

```python
# 记录普通信息
logger.info("这是一条信息")

# 记录警告
logger.warning("这是一条警告")

# 记录错误
logger.error("发生错误", exc_info=True)  # exc_info=True 会记录异常堆栈

# 记录调试信息（不会显示在控制台，但会写入日志文件）
logger.debug("这是一条调试信息")
```

### 3. 记录阶段开始和结束

工作流程中的各个阶段可以使用专门的函数来记录开始和结束：

```python
from utils.logger import log_stage_start, log_stage_end

# 记录阶段开始
log_stage_start(logger, "阶段名称")

# 执行阶段...

# 记录阶段结束
log_stage_end(logger, "阶段名称", success=True, duration=执行时间)
```

### 4. 在主工作流中使用工作流日志记录器

```python
from utils.logger import get_workflow_logger

# 获取工作流日志记录器
logger = get_workflow_logger()
```

## 日志文件位置

所有日志文件都存储在项目根目录下的 `logs` 文件夹中：

- `workflow.log`: 主工作流日志
- `fetch_trends.log`: 趋势获取阶段日志
- `generate_content_langchain.log`: 内容生成阶段日志
- `generate_image.log`: 图片生成阶段日志
- `imgur_upload.log`: Imgur上传阶段日志
- `push_to_notion.log`: Notion推送阶段日志

## 日志级别说明

- **DEBUG**: 详细的调试信息，仅记录到文件中
- **INFO**: 普通信息，记录到控制台和文件中
- **WARNING**: 警告信息，表示潜在问题但不影响主要功能
- **ERROR**: 错误信息，表示功能无法正常执行
- **CRITICAL**: 严重错误，表示程序可能无法继续运行

## 示例：查看日志

可以使用以下命令查看特定模块的日志：

```bash
# 查看主工作流日志
cat logs/workflow.log

# 查看图片上传日志
cat logs/imgur_upload.log

# 查看最新的日志
tail -f logs/workflow.log
``` 