import os
import logging
import warnings
from datetime import datetime
import sys

# Constants
LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# 过滤重复警告的类
class DuplicateFilter:
    """
    过滤重复警告的日志过滤器
    """
    def __init__(self):
        self.msgs = set()
    
    def filter(self, record):
        # 如果是pytrends的FutureWarning，过滤重复的
        if record.levelno == logging.WARNING and "pytrends" in record.msg and "FutureWarning" in record.msg:
            # 保留简短签名，避免日志过长
            sig = record.msg[:100]
            if sig in self.msgs:
                return False
            self.msgs.add(sig)
        return True

def get_logger(stage_name):
    """
    Get a logger for a specific stage that logs to both console and file.
    
    Args:
        stage_name (str): Name of the stage (e.g., "fetch_trends", "generate_content")
        
    Returns:
        logging.Logger: Configured logger for the stage
    """
    # Create logger
    logger = logging.getLogger(stage_name)
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create file handler for this stage
    log_file = os.path.join(LOG_DIR, f"{stage_name}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatters and add to handlers
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add the duplicate filter to both handlers
    duplicate_filter = DuplicateFilter()
    file_handler.addFilter(duplicate_filter)
    console_handler.addFilter(duplicate_filter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_workflow_logger():
    """
    Get a logger for the main workflow that logs to both console and file.
    
    Returns:
        logging.Logger: Configured logger for the main workflow
    """
    return get_logger("workflow")

def log_stage_start(logger, stage_name):
    """
    Log the start of a stage with a standardized format.
    
    Args:
        logger (logging.Logger): The logger to use
        stage_name (str): Name of the stage
    """
    logger.info(f"{'='*20} STARTING {stage_name} {'='*20}")

def log_stage_end(logger, stage_name, success=True, duration=None):
    """
    Log the end of a stage with a standardized format.
    
    Args:
        logger (logging.Logger): The logger to use
        stage_name (str): Name of the stage
        success (bool): Whether the stage was successful
        duration (float, optional): Duration of the stage in seconds
    """
    status = "COMPLETED SUCCESSFULLY" if success else "FAILED"
    duration_str = f" (Duration: {duration:.2f}s)" if duration is not None else ""
    logger.info(f"{'='*20} {status}: {stage_name}{duration_str} {'='*20}")

def log_error(logger, message, exc_info=True):
    """
    Log an error with exception info.
    
    Args:
        logger (logging.Logger): The logger to use
        message (str): Error message
        exc_info (bool): Whether to include exception info
    """
    logger.error(message, exc_info=exc_info)

def filter_warnings():
    """
    过滤不必要的警告信息
    """
    # 忽略pytrends的FutureWarning
    warnings.filterwarnings("once", category=FutureWarning, module="pytrends")
    
    # 可以添加其他警告过滤规则
    
# 在导入时自动应用警告过滤
filter_warnings() 