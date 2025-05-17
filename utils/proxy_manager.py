#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代理管理器 - 使用 web_scraping_toolkit 中的实现
这是一个兼容性包装器，为了保持向后兼容

警告: 此模块已弃用，请直接使用 web_scraping_toolkit 中的 ProxyManager
"""

import logging
import warnings

# 导入 web_scraping_toolkit 中的实现
from web_scraping_toolkit import ProxyManager as WST_ProxyManager

# 获取日志记录器
logger = logging.getLogger("proxy_manager")

# 输出弃用警告
warnings.warn(
    "本地 ProxyManager 类已弃用，请直接使用 web_scraping_toolkit 中的 ProxyManager",
    DeprecationWarning,
    stacklevel=2
)

class ProxyManager(WST_ProxyManager):
    """
    代理管理器，支持SmartProxy和自定义代理
    
    此类是对 web_scraping_toolkit.ProxyManager 的包装，
    为了保持向后兼容
    """
    
    def __init__(self):
        """初始化代理管理器，使用.env配置"""
        # 调用父类初始化
        super().__init__()
        logger.info("使用 web_scraping_toolkit 提供的代理管理器") 