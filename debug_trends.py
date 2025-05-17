import os
import sys
from PIL import Image
import pytesseract  # 注意：这需要安装pytesseract和tesseract-ocr

# 检查是否存在截图目录
screenshot_dir = "data/trend_screenshots"
if not os.path.exists(screenshot_dir):
    print(f"截图目录 {screenshot_dir} 不存在")
    sys.exit(1)

# 列出所有截图文件
screenshots = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
if not screenshots:
    print("没有找到截图文件")
    sys.exit(1)

# 分析最近的几个截图
for i, screenshot in enumerate(sorted(screenshots)[:3]):
    screenshot_path = os.path.join(screenshot_dir, screenshot)
    print(f"\n分析截图 {i+1}/{len(screenshots[:3])}: {screenshot}")
    
    # 打开截图
    img = Image.open(screenshot_path)
    width, height = img.size
    print(f"图片尺寸: {width}x{height}")
    
    # 尝试使用OCR识别图表上的数字
    try:
        # 只分析图表可能在的区域（上部和中间部分）
        chart_region = img.crop((0, 100, width, height-200))
        text = pytesseract.image_to_string(chart_region)
        
        # 寻找可能的趋势数字
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        print(f"OCR识别文本 ({len(lines)} 行):")
        for line in lines[:10]:  # 只显示前10行
            print(f"  - {line}")
        
        # 查找数字
        import re
        numbers = re.findall(r'\d+', text)
        print(f"找到的数字: {numbers[:10]}")  # 只显示前10个数字
        
        # 分析颜色分布，检查是否是图表区域
        # 简单分析 - 检查是否有趋势图表的特征色（Google蓝色等）
        google_blue_count = 0
        for x in range(0, width, 10):
            for y in range(100, height-200, 10):
                try:
                    pixel = img.getpixel((x, y))
                    # 检查是否接近Google蓝色 (大约是 #4285F4)
                    if (len(pixel) >= 3 and 
                        pixel[0] < 100 and 
                        pixel[1] > 100 and pixel[1] < 160 and 
                        pixel[2] > 200):
                        google_blue_count += 1
                except:
                    pass
        
        print(f"可能的Google图表蓝色像素数: {google_blue_count}")
        if google_blue_count > 20:
            print("极有可能是包含Google趋势图表的页面")
        
        # 检查是否有图表Y轴的特征
        has_yaxis = False
        # Y轴通常是垂直的数字刻度线
        for y in range(100, height-200, 50):
            left_pixels = []
            for x in range(50, 150, 5):
                try:
                    pixel = img.getpixel((x, y))
                    left_pixels.append(sum(pixel[:3])/3)  # 平均亮度
                except:
                    pass
            if left_pixels and max(left_pixels) - min(left_pixels) > 50:
                has_yaxis = True
                break
                
        print(f"检测到Y轴: {has_yaxis}")
        
        # 检查是否有错误页面的特征
        error_keywords = ["error", "429", "too many", "rate limit", "访问受限", "错误"]
        error_detected = any(kw.lower() in text.lower() for kw in error_keywords)
        if error_detected:
            print("检测到可能是错误页面!")
            error_lines = [line for line in lines if any(kw.lower() in line.lower() for kw in error_keywords)]
            for line in error_lines:
                print(f"  错误内容: {line}")
    
    except Exception as e:
        print(f"分析过程中出错: {e}")

print("\n分析总结:")
print("1. 从截图内容看，Google Trends页面可能有以下问题:")
print("   - 可能是非标准的页面结构或Google更改了DOM结构")
print("   - 页面可能显示了错误信息或限流提示")
print("   - 页面可能尚未完全加载趋势数据")
print("2. 建议采取的改进措施:")
print("   - 增加页面加载等待时间")
print("   - 尝试使用不同的CSS选择器")
print("   - 添加更多的页面识别逻辑")
print("   - 考虑更多的代理和IP轮换以避免限流") 