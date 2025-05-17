#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import argparse
from PIL import Image
import logging
from pathlib import Path

# 检查pytesseract是否可用
PYTESSERACT_AVAILABLE = False
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pass

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/analyze_trends.log")
    ]
)

logger = logging.getLogger("analyze_trends")

def analyze_screenshot(screenshot_path):
    """分析截图，尝试提取有用的信息，用于调试"""
    try:
        if not os.path.exists(screenshot_path):
            logger.error(f"截图不存在: {screenshot_path}")
            return
            
        logger.info(f"分析截图: {screenshot_path}")
        
        # 读取图像
        img = Image.open(screenshot_path)
        width, height = img.size
        logger.info(f"图片尺寸: {width}x{height}")
        
        # 检查OCR是否可用
        if PYTESSERACT_AVAILABLE:
            logger.info("OCR工具可用，将进行文本识别")
            # 分割图像为不同区域
            regions = {
                "top": (0, 0, width, 150),         # 顶部导航区
                "chart": (0, 150, width, height-200),  # 中间图表区
                "bottom": (0, height-200, width, height) # 底部区域
            }
            
            # 对每个区域进行OCR识别
            for region_name, bbox in regions.items():
                try:
                    region_img = img.crop(bbox)
                    text = pytesseract.image_to_string(region_img)
                    
                    # 过滤空行
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    logger.info(f"区域 '{region_name}' 识别出 {len(lines)} 行文本")
                    for line in lines[:5]:  # 只显示前5行
                        logger.info(f"  - {line}")
                        
                    # 查找数字
                    numbers = []
                    for line in lines:
                        nums = re.findall(r'\b(\d{1,3})\b', line)
                        try:
                            numbers.extend([int(n) for n in nums if 0 < int(n) <= 100])
                        except ValueError:
                            pass
                        
                    if numbers:
                        logger.info(f"  找到可能的趋势值: {numbers}")
                        avg = sum(numbers) / len(numbers)
                        logger.info(f"  平均值: {avg:.1f}")
                except Exception as e:
                    logger.warning(f"OCR区域 '{region_name}' 失败: {e}")
        else:
            logger.warning("OCR工具不可用，跳过文本识别")
                
        # 分析图像特征 - 即使没有OCR也可以进行
        logger.info("分析图像特征")
        
        # 检查是否可能是错误页面
        # 错误页面通常有较多的白色区域
        white_pixels = 0
        sample_step = 10  # 采样步长，减少计算量
        for x in range(0, width, sample_step):
            for y in range(0, height, sample_step):
                pixel = img.getpixel((x, y))
                # 检查是否接近白色
                if all(v > 240 for v in pixel[:3]):
                    white_pixels += 1
                    
        total_samples = (width // sample_step) * (height // sample_step)
        white_ratio = white_pixels / total_samples
        logger.info(f"白色像素比例: {white_ratio:.2f}")
        
        # 检查是否有Google趋势图表的特征色
        color_counts = {
            "blue": 0,  # Google蓝色 (#4285F4)
            "red": 0,   # 红色
            "green": 0, # 绿色
            "yellow": 0 # 黄色
        }
        
        # 仅分析图表区域
        chart_area = (0, 150, width, height-200)
        
        for x in range(chart_area[0], chart_area[2], sample_step):
            for y in range(chart_area[1], chart_area[3], sample_step):
                pixel = img.getpixel((x, y))
                if len(pixel) >= 3:
                    r, g, b = pixel[:3]
                    
                    # 检测蓝色 (Google蓝色或近似色)
                    if b > 200 and r < 100 and g < 160 and g > 80:
                        color_counts["blue"] += 1
                    
                    # 检测红色
                    if r > 200 and g < 100 and b < 100:
                        color_counts["red"] += 1
                    
                    # 检测绿色
                    if g > 200 and r < 100 and b < 100:
                        color_counts["green"] += 1
                    
                    # 检测黄色
                    if r > 200 and g > 200 and b < 100:
                        color_counts["yellow"] += 1
                
        # 计算图表区域总像素样本数
        chart_samples = ((chart_area[2] - chart_area[0]) // sample_step) * ((chart_area[3] - chart_area[1]) // sample_step)
        
        # 输出各颜色比例
        for color, count in color_counts.items():
            ratio = count / chart_samples if chart_samples > 0 else 0
            logger.info(f"图表区域{color}色像素比例: {ratio:.4f} ({count}/{chart_samples})")
        
        # 检查是否有图表网格线特征
        # 图表网格线通常是浅灰色的水平/垂直线
        grid_lines = 0
        for y in range(chart_area[1], chart_area[3], 20):  # 每20像素采样一行
            line_pixels = []
            for x in range(chart_area[0], chart_area[2], 5):
                pixel = img.getpixel((x, y))
                # 浅灰色的RGB值大致相等，且在180-240之间
                if all(180 <= v <= 240 for v in pixel[:3]) and max(pixel[:3]) - min(pixel[:3]) < 10:
                    line_pixels.append(1)
                else:
                    line_pixels.append(0)
            
            # 检查是否存在连续的网格线像素
            grid_line_segments = 0
            current_segment = 0
            for p in line_pixels:
                if p == 1:
                    current_segment += 1
                else:
                    if current_segment >= 10:  # 至少10个连续像素才算一段网格线
                        grid_line_segments += 1
                    current_segment = 0
            
            # 最后一段也要检查
            if current_segment >= 10:
                grid_line_segments += 1
                
            grid_lines += grid_line_segments
        
        logger.info(f"检测到疑似网格线数量: {grid_lines}")
        
        # 检查是否可能有图表Y轴刻度
        # Y轴刻度通常位于图表左侧
        y_axis_features = 0
        left_margin = 100  # 假设Y轴刻度位于左边距100像素内
        
        for y in range(chart_area[1], chart_area[3], 30):
            has_dark_pixel = False
            for x in range(chart_area[0], chart_area[0] + left_margin):
                pixel = img.getpixel((x, y))
                # 深色文本像素
                if all(v < 100 for v in pixel[:3]):
                    has_dark_pixel = True
                    break
            
            if has_dark_pixel:
                y_axis_features += 1
        
        logger.info(f"检测到疑似Y轴刻度特征数量: {y_axis_features}")
        
        # 综合分析
        has_chart_features = False
        if color_counts["blue"] > 50 or grid_lines > 3 or y_axis_features > 2:
            has_chart_features = True
        
        # 结论
        if has_chart_features:
            logger.info("检测到图表特征，页面可能包含趋势图表")
            
            # 尝试从图像特征估算趋势值
            # 方法: 检测图表中线条的平均高度位置
            try:
                # 首先确定图表区域，假设在页面中部
                chart_y_start = height // 3
                chart_y_end = height * 2 // 3
                chart_height = chart_y_end - chart_y_start
                
                # 检测数据线位置
                line_y_positions = []
                
                for y in range(chart_y_start, chart_y_end):
                    line_pixel_count = 0
                    for x in range(width // 4, width * 3 // 4):  # 只检查图表中部区域
                        pixel = img.getpixel((x, y))
                        # 检测是否是数据线颜色 (蓝色)
                        if len(pixel) >= 3 and pixel[2] > 200 and pixel[0] < 100:
                            line_pixel_count += 1
                    
                    # 如果一行中有足够多的数据线像素，记录该行位置
                    if line_pixel_count > 5:
                        line_y_positions.append(y)
                
                if line_y_positions:
                    # 计算平均位置
                    avg_y = sum(line_y_positions) / len(line_y_positions)
                    # 转换为相对位置 (0-1范围)
                    relative_pos = (avg_y - chart_y_start) / chart_height
                    # 转换为趋势分数 (0-100范围)，越高分数越高
                    estimated_score = 100 - int(relative_pos * 100)
                    
                    logger.info(f"基于图表位置估计的趋势分数: {estimated_score}")
            except Exception as e:
                logger.warning(f"估计趋势分数失败: {e}")
                
        elif white_ratio > 0.9:
            logger.info("检测到大量白色区域，页面可能是错误页面或加载中")
        else:
            logger.info("页面特征不明确，可能需要人工分析")
        
        logger.info("分析完成")
        
    except Exception as e:
        logger.error(f"分析截图失败: {e}")


def list_screenshots():
    """列出所有的截图文件"""
    screenshots_dir = "data/trend_screenshots"
    if not os.path.exists(screenshots_dir):
        logger.error(f"截图目录不存在: {screenshots_dir}")
        return
        
    screenshots = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
    if not screenshots:
        logger.info("未找到截图")
        return
        
    logger.info(f"找到 {len(screenshots)} 个截图:")
    screenshots.sort(key=lambda f: os.path.getmtime(os.path.join(screenshots_dir, f)), reverse=True)
    
    for i, screenshot in enumerate(screenshots[:10]):  # 只显示最新的10个
        file_path = os.path.join(screenshots_dir, screenshot)
        file_size = os.path.getsize(file_path) // 1024  # KB
        file_time = os.path.getmtime(file_path)
        
        # 识别趋势关键词
        keyword = None
        parts = screenshot.split('_')
        if len(parts) >= 2:
            keyword = ' '.join(parts[1:-1]).replace('_', ' ')
        
        if keyword:
            logger.info(f"{i+1}. {screenshot} - '{keyword}' ({file_size}KB)")
        else:
            logger.info(f"{i+1}. {screenshot} ({file_size}KB)")
    
    if len(screenshots) > 10:
        logger.info(f"... 还有 {len(screenshots)-10} 个截图未显示")


def analyze_all_screenshots(max_count=5):
    """分析最近的几个截图"""
    screenshots_dir = "data/trend_screenshots"
    if not os.path.exists(screenshots_dir):
        logger.error(f"截图目录不存在: {screenshots_dir}")
        return
        
    screenshots = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
    if not screenshots:
        logger.info("未找到截图")
        return
        
    # 按修改时间排序，最新的在前
    screenshots.sort(key=lambda f: os.path.getmtime(os.path.join(screenshots_dir, f)), reverse=True)
    
    # 分析最近的几个
    for screenshot in screenshots[:max_count]:
        file_path = os.path.join(screenshots_dir, screenshot)
        analyze_screenshot(file_path)
        logger.info("-" * 50)  # 分隔线


def export_trends_data():
    """将提取的趋势数据导出到JSON文件"""
    screenshots_dir = "data/trend_screenshots"
    if not os.path.exists(screenshots_dir):
        logger.error(f"截图目录不存在: {screenshots_dir}")
        return
        
    screenshots = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
    if not screenshots:
        logger.info("未找到截图")
        return
    
    trends_data = {}
    
    # 从文件名解析关键词
    for screenshot in screenshots:
        try:
            # 文件名格式: trend_Keyword_Timestamp.png
            parts = screenshot.split('_')
            if len(parts) >= 3:
                keyword = parts[1]
                # 如果有多个下划线，组合为完整关键词
                if len(parts) > 3:
                    keyword = '_'.join(parts[1:-1])
                
                # 提取时间戳
                timestamp = int(parts[-1].split('.')[0])
                
                # 初始化关键词数据
                if keyword not in trends_data:
                    trends_data[keyword] = []
                
                # 添加截图记录
                trends_data[keyword].append({
                    "timestamp": timestamp,
                    "filepath": os.path.join(screenshots_dir, screenshot)
                })
        except Exception as e:
            logger.warning(f"解析文件名失败: {screenshot} - {e}")
    
    # 为每个关键词分析图像并提取趋势值
    for keyword, screenshots in trends_data.items():
        logger.info(f"分析关键词 '{keyword}' 的 {len(screenshots)} 个截图")
        
        for screenshot in screenshots:
            try:
                # 使用像素分析方法估算趋势值
                img = Image.open(screenshot["filepath"])
                width, height = img.size
                
                # 图表区域
                chart_area = (0, height//3, width, height*2//3)
                
                # 检测蓝色数据线的位置
                line_y_positions = []
                
                for y in range(chart_area[1], chart_area[3]):
                    blue_pixels = 0
                    for x in range(chart_area[0], chart_area[2], 5):
                        pixel = img.getpixel((x, y))
                        if len(pixel) >= 3:
                            r, g, b = pixel[:3]
                            if b > 200 and r < 100 and g < 160:
                                blue_pixels += 1
                    
                    if blue_pixels > 5:  # 该行有足够多的蓝色像素
                        line_y_positions.append(y)
                
                if line_y_positions:
                    avg_y = sum(line_y_positions) / len(line_y_positions)
                    # 相对位置，从下到上为0到1
                    relative_pos = (chart_area[3] - avg_y) / (chart_area[3] - chart_area[1])
                    # 转换为0-100的热度值
                    trend_score = int(relative_pos * 100)
                    
                    screenshot["estimated_value"] = trend_score
                    logger.info(f"  估算趋势值: {trend_score}")
                else:
                    screenshot["estimated_value"] = None
                    logger.info("  未能估算趋势值")
            
            except Exception as e:
                logger.warning(f"分析截图失败: {screenshot['filepath']} - {e}")
                screenshot["estimated_value"] = None
    
    # 输出结果
    output_path = "data/extracted_trends.json"
    with open(output_path, 'w') as f:
        json.dump(trends_data, f, indent=2)
    
    logger.info(f"趋势数据已导出到: {output_path}")


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Google Trends截图分析工具")
    parser.add_argument("--file", help="分析指定的截图文件")
    parser.add_argument("--list", action="store_true", help="列出所有截图")
    parser.add_argument("--all", action="store_true", help="分析所有截图")
    parser.add_argument("--count", type=int, default=5, help="分析的截图数量")
    parser.add_argument("--export", action="store_true", help="导出趋势数据到JSON")
    
    args = parser.parse_args()
    
    if args.file:
        analyze_screenshot(args.file)
    elif args.list:
        list_screenshots()
    elif args.all:
        analyze_all_screenshots(args.count)
    elif args.export:
        export_trends_data()
    else:
        parser.print_help() 