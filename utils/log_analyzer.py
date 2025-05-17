#!/usr/bin/env python
"""
日志分析工具 - 用于分析工作流日志文件并提供摘要和错误分析
"""

import os
import re
import json
import argparse
from datetime import datetime
from collections import Counter, defaultdict

# 日志文件目录
LOG_DIR = "logs"

# 日志级别颜色（终端ANSI颜色代码）
COLORS = {
    "INFO": "\033[32m",     # 绿色
    "WARNING": "\033[33m",  # 黄色
    "ERROR": "\033[31m",    # 红色
    "CRITICAL": "\033[35m", # 紫色
    "DEBUG": "\033[36m",    # 青色
    "RESET": "\033[0m"      # 重置
}

def colorize(text, level):
    """给文本添加颜色"""
    color = COLORS.get(level, COLORS["RESET"])
    return f"{color}{text}{COLORS['RESET']}"

def parse_log_line(line):
    """解析单行日志"""
    # 日志格式: 2023-05-12 10:30:45 - module_name - LEVEL - message
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (\w+) - (.+)"
    match = re.match(pattern, line)
    if match:
        timestamp, module, level, message = match.groups()
        return {
            "timestamp": timestamp,
            "module": module,
            "level": level,
            "message": message.strip()
        }
    return None

def get_all_log_files():
    """获取所有日志文件"""
    if not os.path.exists(LOG_DIR):
        return []
    
    return [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.endswith('.log')]

def get_workflow_json_files():
    """获取所有工作流JSON日志文件"""
    if not os.path.exists(LOG_DIR):
        return []
    
    return [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.startswith('xhs_workflow_') and f.endswith('.json')]

def analyze_log_file(log_file, verbose=False):
    """分析单个日志文件"""
    if not os.path.exists(log_file):
        print(f"日志文件不存在: {log_file}")
        return None
    
    module_name = os.path.basename(log_file).replace('.log', '')
    
    stats = {
        "file": log_file,
        "module": module_name,
        "total_lines": 0,
        "level_counts": Counter(),
        "first_timestamp": None,
        "last_timestamp": None,
        "duration": None,
        "errors": [],
        "warnings": []
    }
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            stats["total_lines"] += 1
            parsed = parse_log_line(line)
            if parsed:
                stats["level_counts"][parsed["level"]] += 1
                
                # 记录时间戳
                timestamp = datetime.strptime(parsed["timestamp"], "%Y-%m-%d %H:%M:%S")
                if stats["first_timestamp"] is None or timestamp < stats["first_timestamp"]:
                    stats["first_timestamp"] = timestamp
                if stats["last_timestamp"] is None or timestamp > stats["last_timestamp"]:
                    stats["last_timestamp"] = timestamp
                
                # 记录错误和警告
                if parsed["level"] == "ERROR":
                    stats["errors"].append(parsed["message"])
                    if verbose:
                        print(colorize(f"ERROR in {module_name}: {parsed['message']}", "ERROR"))
                elif parsed["level"] == "WARNING":
                    stats["warnings"].append(parsed["message"])
                    if verbose:
                        print(colorize(f"WARNING in {module_name}: {parsed['message']}", "WARNING"))
    
    # 计算持续时间
    if stats["first_timestamp"] and stats["last_timestamp"]:
        stats["duration"] = (stats["last_timestamp"] - stats["first_timestamp"]).total_seconds()
        stats["first_timestamp"] = stats["first_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        stats["last_timestamp"] = stats["last_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    
    return stats

def analyze_workflow_json(json_file):
    """分析工作流JSON日志文件"""
    if not os.path.exists(json_file):
        print(f"工作流日志文件不存在: {json_file}")
        return None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析时间戳并计算总持续时间
        start_time = datetime.fromisoformat(data.get("start_time", ""))
        end_time = datetime.fromisoformat(data.get("end_time", ""))
        duration = (end_time - start_time).total_seconds()
        
        # 整理每个步骤的状态
        steps_status = []
        for step in data.get("steps", []):
            step_name = step.get("name", "")
            step_success = step.get("success", False)
            steps_status.append((step_name, step_success))
        
        return {
            "file": json_file,
            "workflow_name": data.get("workflow_name", ""),
            "overall_status": data.get("overall_status", ""),
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": duration,
            "steps": steps_status,
            "content_count": data.get("content_count", 0)
        }
    except Exception as e:
        print(f"解析工作流日志文件失败: {e}")
        return None

def print_summary(log_stats):
    """打印日志分析摘要"""
    if not log_stats:
        print("没有可分析的日志文件")
        return
    
    print("\n" + "="*50)
    print(f"日志分析摘要 ({len(log_stats)} 个日志文件)")
    print("="*50)
    
    # 按模块分组统计错误和警告
    modules_with_errors = defaultdict(int)
    modules_with_warnings = defaultdict(int)
    total_errors = 0
    total_warnings = 0
    
    for stats in log_stats:
        module = stats["module"]
        error_count = len(stats["errors"])
        warning_count = len(stats["warnings"])
        
        if error_count > 0:
            modules_with_errors[module] = error_count
            total_errors += error_count
        
        if warning_count > 0:
            modules_with_warnings[module] = warning_count
            total_warnings += warning_count
    
    # 打印总体统计
    print(f"\n总错误数: {colorize(str(total_errors), 'ERROR')}")
    print(f"总警告数: {colorize(str(total_warnings), 'WARNING')}")
    
    # 打印每个模块的统计
    print("\n模块统计:")
    for stats in log_stats:
        module = stats["module"]
        duration_str = f"{stats['duration']:.2f}秒" if stats["duration"] else "N/A"
        error_str = colorize(f"{len(stats['errors'])}", "ERROR") if stats["errors"] else "0"
        warning_str = colorize(f"{len(stats['warnings'])}", "WARNING") if stats["warnings"] else "0"
        
        print(f"- {module}: 日志行数 {stats['total_lines']}, 持续时间 {duration_str}, 错误 {error_str}, 警告 {warning_str}")
    
    # 打印错误列表
    if total_errors > 0:
        print("\n错误列表:")
        for module, count in modules_with_errors.items():
            print(f"\n{module} ({count} 个错误):")
            for stats in log_stats:
                if stats["module"] == module:
                    for i, error in enumerate(stats["errors"][:5], 1):  # 只显示前5个错误
                        print(f"  {i}. {colorize(error, 'ERROR')}")
                    if len(stats["errors"]) > 5:
                        print(f"  ... 还有 {len(stats['errors']) - 5} 个错误未显示")

def print_workflow_summary(workflow_stats):
    """打印工作流执行摘要"""
    if not workflow_stats:
        print("没有可分析的工作流日志文件")
        return
    
    print("\n" + "="*50)
    print(f"工作流执行摘要 ({len(workflow_stats)} 个工作流)")
    print("="*50)
    
    # 按时间倒序排序
    sorted_stats = sorted(workflow_stats, key=lambda x: x["start_time"], reverse=True)
    
    for stats in sorted_stats:
        workflow_name = stats["workflow_name"]
        status = stats["overall_status"]
        duration = f"{stats['duration']:.2f}秒" if stats["duration"] else "N/A"
        
        status_color = "ERROR" if status == "失败" else "INFO"
        
        print(f"\n工作流: {workflow_name}")
        print(f"状态: {colorize(status, status_color)}")
        print(f"执行时间: {stats['start_time']} - {stats['end_time']} (持续时间: {duration})")
        
        if "content_count" in stats and stats["content_count"] > 0:
            print(f"生成内容数量: {stats['content_count']}")
        
        print("步骤执行情况:")
        for step_name, step_success in stats["steps"]:
            status_str = colorize("成功", "INFO") if step_success else colorize("失败", "ERROR")
            print(f"- {step_name}: {status_str}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="小红书工作流日志分析工具")
    parser.add_argument("--file", "-f", help="指定要分析的日志文件")
    parser.add_argument("--all", "-a", action="store_true", help="分析所有日志文件")
    parser.add_argument("--workflow", "-w", action="store_true", help="分析工作流执行情况")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    args = parser.parse_args()
    
    # 分析单个日志文件
    if args.file:
        log_file = args.file
        if not os.path.exists(log_file):
            log_file = os.path.join(LOG_DIR, log_file)
        
        if os.path.exists(log_file):
            stats = analyze_log_file(log_file, args.verbose)
            if stats:
                print_summary([stats])
        else:
            print(f"日志文件不存在: {args.file}")
    
    # 分析所有日志文件
    elif args.all:
        log_files = get_all_log_files()
        if log_files:
            log_stats = []
            for log_file in log_files:
                stats = analyze_log_file(log_file, args.verbose)
                if stats:
                    log_stats.append(stats)
            print_summary(log_stats)
        else:
            print("未找到任何日志文件")
    
    # 分析工作流执行情况
    elif args.workflow:
        workflow_files = get_workflow_json_files()
        if workflow_files:
            workflow_stats = []
            for workflow_file in workflow_files:
                stats = analyze_workflow_json(workflow_file)
                if stats:
                    workflow_stats.append(stats)
            print_workflow_summary(workflow_stats)
        else:
            print("未找到任何工作流日志文件")
    
    # 默认行为
    else:
        # 默认分析工作流日志和所有日志文件
        workflow_files = get_workflow_json_files()
        if workflow_files:
            workflow_stats = []
            for workflow_file in workflow_files:
                stats = analyze_workflow_json(workflow_file)
                if stats:
                    workflow_stats.append(stats)
            print_workflow_summary(workflow_stats)
        
        log_files = get_all_log_files()
        if log_files:
            log_stats = []
            for log_file in log_files:
                stats = analyze_log_file(log_file, args.verbose)
                if stats:
                    log_stats.append(stats)
            print_summary(log_stats)

if __name__ == "__main__":
    main() 