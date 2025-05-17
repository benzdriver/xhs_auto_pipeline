#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test each extraction method for Google Trends separately
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the extraction methods
from stages.fetch_trends import (
    extract_method1_datapoints,
    extract_method2_javascript,
    extract_method3_selectors,
    extract_method4_svg_elements,
    extract_method5_ocr
)

def test_extraction_methods():
    """Test each extraction method on Google Trends"""
    print("Testing Google Trends data extraction methods")
    
    test_keyword = "Canadian immigration"
    screenshot_dir = "test_screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use non-headless for visual inspection
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate directly to Google Trends
        url = f"https://trends.google.com/trends/explore?date=now%207-d&geo=CA&q={test_keyword.replace(' ', '%20')}"
        print(f"Loading Google Trends page: {url}")
        
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            print("✓ Page loaded, waiting for content to render...")
            time.sleep(10)  # Wait for chart to render
            
            # Take screenshot for analysis
            screenshot_path = os.path.join(screenshot_dir, f"trends_{int(time.time())}.png")
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            # Test each extraction method
            methods = [
                ("Method 1: Datapoints Position", extract_method1_datapoints),
                ("Method 2: JavaScript Data", extract_method2_javascript),
                ("Method 3: CSS Selectors", extract_method3_selectors),
                ("Method 4: SVG Elements", extract_method4_svg_elements),
                ("Method 5: OCR", extract_method5_ocr)
            ]
            
            for name, method in methods:
                print(f"\nTesting {name}...")
                try:
                    result = method(page, test_keyword, screenshot_path)
                    if result is not None:
                        print(f"✓ Success! Extracted score: {result}")
                    else:
                        print("✗ Method returned None")
                except Exception as e:
                    print(f"✗ Error: {e}")
            
        except Exception as e:
            print(f"✗ Failed to load page: {e}")
        
        browser.close()

if __name__ == "__main__":
    test_extraction_methods() 