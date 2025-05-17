#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 web_scraping_toolkit 服务组件
"""

# 从 web_scraping_toolkit 导入组件
from web_scraping_toolkit import ProxyManager, CaptchaSolver

print("=== 测试 web_scraping_toolkit 服务组件 ===")

# 测试代理
print("\n测试代理服务:")
try:
    proxy_manager = ProxyManager()
    print(f"代理启用状态: {proxy_manager.proxy_enabled if hasattr(proxy_manager, 'proxy_enabled') else '未知'}")
    print(f"可用代理数量: {len(proxy_manager.proxy_list) if hasattr(proxy_manager, 'proxy_list') else '未知'}")
    proxy = proxy_manager.get_proxy() if hasattr(proxy_manager, 'get_proxy') else None
    print(f"当前代理: {proxy}")
    test_result = proxy_manager.test_proxy() if hasattr(proxy_manager, 'test_proxy') else False
    print(f"代理测试结果: {'成功' if test_result else '失败'}")
except Exception as e:
    print(f"代理服务测试失败: {e}")

# 测试验证码服务
print("\n测试验证码服务:")
try:
    captcha_solver = CaptchaSolver()
    is_available = captcha_solver.is_available() if hasattr(captcha_solver, 'is_available') else False
    print(f"验证码服务可用: {is_available}")
    
    if hasattr(captcha_solver, 'get_balance'):
        balance = captcha_solver.get_balance()
        print(f"2Captcha 账户余额: ${balance}")
    else:
        print("无法获取账户余额，方法不可用")
except Exception as e:
    print(f"验证码服务测试失败: {e}")

print("\n测试完成！")
