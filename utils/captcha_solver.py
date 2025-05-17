#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证码解决器 - 使用 web_scraping_toolkit 中的实现
这是一个兼容性包装器，为了保持向后兼容

警告: 此模块已弃用，请直接使用 web_scraping_toolkit 中的 CaptchaSolver
"""

import logging
import warnings

# 导入 web_scraping_toolkit 中的实现
from web_scraping_toolkit import CaptchaSolver as WST_CaptchaSolver

# 获取日志记录器
logger = logging.getLogger("captcha_solver")

# 输出弃用警告
warnings.warn(
    "本地 CaptchaSolver 类已弃用，请直接使用 web_scraping_toolkit 中的 CaptchaSolver",
    DeprecationWarning,
    stacklevel=2
)

class CaptchaSolver(WST_CaptchaSolver):
    """
    验证码解决工具类，支持2Captcha服务
    
    此类是对 web_scraping_toolkit.CaptchaSolver 的包装，
    为了保持向后兼容
    """
    
    def __init__(self):
        """初始化验证码解决器，使用.env配置"""
        # 调用父类初始化
        super().__init__()
        logger.info("使用 web_scraping_toolkit 提供的验证码解决器") 