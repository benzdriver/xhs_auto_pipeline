import requests

# 测试不同的代理协议和格式

# 测试URL列表
urls = [
    'https://ip.decodo.com/json',  # Decodo的IP检查服务
    'https://api.ipify.org?format=json',  # 公共IP检查服务
    'https://httpbin.org/ip'  # 另一个公共IP检查服务
]

# 1. 标准HTTP代理
print("\n=== 测试标准HTTP代理 ===")
username = 'sppccpq0sd'
password = 'pYcSbwgM65Mt2jy6m~'
proxy = f"http://{username}:{password}@gate.decodo.com:10001"

print(f"测试代理连接: {proxy.replace(password, '****')}")

for url in urls:
    print(f"\n尝试URL: {url}")
    try:
        result = requests.get(url, proxies = {
            'http': proxy,
            'https': proxy
        }, timeout=10)
        
        print(f"状态码: {result.status_code}")
        print(f"响应内容: {result.text[:200]}")  # 只显示前200个字符
    except Exception as e:
        print(f"错误: {e}")

# 2. 尝试SOCKS5代理
try:
    import socks
    import urllib3.contrib.socks
    print("\n=== 测试SOCKS5代理 ===")
    
    # 安装socks支持
    print("已安装SOCKS支持库")
except ImportError:
    print("\n=== 未安装SOCKS支持库，请运行: pip install requests[socks] ===")
    
    # 尝试安装
    try:
        import subprocess
        print("尝试安装SOCKS支持库...")
        subprocess.check_call(["pip", "install", "requests[socks]"])
        import socks
        import urllib3.contrib.socks
        print("安装成功!")
    except Exception as e:
        print(f"安装失败: {e}")
        exit(1)

# 使用SOCKS5协议
socks5_proxy = f"socks5://{username}:{password}@gate.decodo.com:7000"
print(f"测试SOCKS5代理连接: {socks5_proxy.replace(password, '****')}")

for url in urls:
    print(f"\n尝试URL: {url}")
    try:
        result = requests.get(url, proxies = {
            'http': socks5_proxy,
            'https': socks5_proxy
        }, timeout=10)
        
        print(f"状态码: {result.status_code}")
        print(f"响应内容: {result.text[:200]}")
    except Exception as e:
        print(f"错误: {e}")

# 3. 尝试使用不同的端口
print("\n=== 测试不同端口 ===")
ports = ["10001", "10002", "10003", "10004", "10005", "10006", "10007"]

for port in ports:
    proxy_port = f"http://{username}:{password}@gate.decodo.com:{port}"
    print(f"\n测试端口 {port}: {proxy_port.replace(password, '****')}")
    
    try:
        result = requests.get(urls[0], proxies = {
            'http': proxy_port,
            'https': proxy_port
        }, timeout=5)
        
        print(f"状态码: {result.status_code}")
        print(f"响应内容: {result.text[:200]}")
        
        # 如果成功，尝试其他URL
        for url in urls[1:]:
            print(f"尝试URL: {url}")
            result = requests.get(url, proxies = {
                'http': proxy_port,
                'https': proxy_port
            }, timeout=5)
            print(f"状态码: {result.status_code}")
            print(f"响应内容: {result.text[:200]}")
            
        # 如果成功，跳出循环
        print("成功找到可用端口!")
        break
    except Exception as e:
        print(f"错误: {e}")

# 4. 尝试使用session格式的用户名
print("\n=== 测试session格式用户名 ===")
username_alt = f"user-{username}-session-1"
proxy_alt = f"http://{username_alt}:{password}@gate.decodo.com:10001"

print(f"测试代理连接: {proxy_alt.replace(password, '****')}")

for url in urls:
    print(f"\n尝试URL: {url}")
    try:
        result = requests.get(url, proxies = {
            'http': proxy_alt,
            'https': proxy_alt
        }, timeout=10)
        
        print(f"状态码: {result.status_code}")
        print(f"响应内容: {result.text[:200]}")
    except Exception as e:
        print(f"错误: {e}")

# 5. 尝试使用socks5h协议(解析主机名)
print("\n=== 测试SOCKS5H协议 ===")
socks5h_proxy = f"socks5h://{username}:{password}@gate.decodo.com:7000"
print(f"测试SOCKS5H代理连接: {socks5h_proxy.replace(password, '****')}")

for url in urls:
    print(f"\n尝试URL: {url}")
    try:
        result = requests.get(url, proxies = {
            'http': socks5h_proxy,
            'https': socks5h_proxy
        }, timeout=10)
        
        print(f"状态码: {result.status_code}")
        print(f"响应内容: {result.text[:200]}")
    except Exception as e:
        print(f"错误: {e}") 