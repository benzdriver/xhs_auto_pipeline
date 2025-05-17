#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import threading
from enum import Enum
import logging

class IndicatorType(Enum):
    """进度指示器类型"""
    SPINNER = 1  # 旋转指示器
    DOTS = 2     # 点动画
    PULSE = 3    # 脉冲动画
    BOUNCE = 4   # 弹跳动画

class ProgressIndicator:
    """
    进度指示器类，用于显示长时间运行任务的进度
    
    使用方法:
    ```python
    # 创建并启动进度指示器
    indicator = ProgressIndicator("正在生成内容", IndicatorType.SPINNER)
    indicator.start()
    
    try:
        # 执行长时间运行的任务
        do_long_running_task()
    finally:
        # 停止指示器
        indicator.stop("内容生成完成!")
    ```
    """
    
    def __init__(self, message="处理中", indicator_type=IndicatorType.SPINNER, 
                 update_interval=0.1, file=sys.stdout, logger=None):
        """
        初始化进度指示器
        
        Args:
            message: 显示的消息
            indicator_type: 指示器类型
            update_interval: 动画更新间隔(秒)
            file: 输出文件对象
            logger: 记录器对象，如果提供则同时记录到日志
        """
        self.message = message
        self.indicator_type = indicator_type
        self.update_interval = update_interval
        self.file = file
        self.logger = logger
        self._running = False
        self._thread = None
        self._start_time = None
        
        # 设置动画帧
        if indicator_type == IndicatorType.SPINNER:
            self._frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        elif indicator_type == IndicatorType.DOTS:
            self._frames = "⣾⣽⣻⢿⡿⣟⣯⣷"
        elif indicator_type == IndicatorType.PULSE:
            self._frames = "█▓▒░ ░▒▓█"
        elif indicator_type == IndicatorType.BOUNCE:
            self._frames = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"
        
    def _animate(self):
        """动画循环"""
        frame_index = 0
        last_message = ""
        
        while self._running:
            frame = self._frames[frame_index % len(self._frames)]
            elapsed = time.time() - self._start_time
            
            # 构建消息
            if elapsed < 60:
                time_str = f"{elapsed:.1f}秒"
            else:
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                time_str = f"{minutes}分{seconds}秒"
            
            message = f"\r{frame} {self.message} ({time_str}) "
            
            # 仅当消息变化时输出
            if message != last_message:
                print(message, end="", file=self.file)
                self.file.flush()
                last_message = message
            
            frame_index += 1
            time.sleep(self.update_interval)
    
    def start(self):
        """启动进度指示器"""
        if self._running:
            return
            
        self._running = True
        self._start_time = time.time()
        
        # 记录开始消息
        if self.logger:
            self.logger.info(f"{self.message} 开始...")
        
        # 启动动画线程
        self._thread = threading.Thread(target=self._animate)
        self._thread.daemon = True
        self._thread.start()
        
    def stop(self, completion_message=None):
        """
        停止进度指示器
        
        Args:
            completion_message: 完成消息，如果为None则使用原始消息
        """
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.update_interval*2)
        
        elapsed = time.time() - self._start_time
        if elapsed < 60:
            time_str = f"{elapsed:.1f}秒"
        else:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            time_str = f"{minutes}分{seconds}秒"
        
        # 显示完成消息
        final_message = completion_message if completion_message else f"{self.message}完成"
        print(f"\r✓ {final_message} (用时{time_str})")
        
        # 记录完成消息
        if self.logger:
            self.logger.info(f"{final_message} (用时{time_str})")

# 全局辅助函数
def with_progress(func, message="处理中", indicator_type=IndicatorType.SPINNER, logger=None):
    """
    装饰器：使用进度指示器执行函数
    
    Args:
        func: 要执行的函数
        message: 显示的消息
        indicator_type: 指示器类型
        logger: 记录器对象
        
    Returns:
        函数的返回值
    """
    indicator = ProgressIndicator(message, indicator_type, logger=logger)
    indicator.start()
    
    try:
        result = func()
        indicator.stop(f"{message}完成")
        return result
    except Exception as e:
        indicator.stop(f"{message}失败: {str(e)}")
        raise e

# 使用示例
if __name__ == "__main__":
    # 简单的例子
    print("简单进度指示器示例:")
    indicator = ProgressIndicator("正在处理数据", IndicatorType.SPINNER)
    indicator.start()
    
    # 模拟长时间运行的任务
    time.sleep(3)
    
    indicator.stop("数据处理完成!")
    
    # 不同的指示器类型
    for indicator_type in IndicatorType:
        print(f"\n{indicator_type.name} 指示器示例:")
        indicator = ProgressIndicator(f"示例 {indicator_type.name}", indicator_type)
        indicator.start()
        time.sleep(2)
        indicator.stop() 