#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Playwright test to check basic connectivity without any automation detection avoidance
"""

import time
from playwright.sync_api import sync_playwright

def run_simple_test():
    print("Starting simple Playwright test")
    
    with sync_playwright() as p:
        for browser_type in ["chromium", "firefox"]:
            print(f"\nTesting with {browser_type} browser:")
            browser = getattr(p, browser_type).launch(headless=False)  # Use non-headless for better testing
            context = browser.new_context()
            page = context.new_page()
            
            # Test simple sites first
            print("Testing connection to example.com...")
            try:
                page.goto("https://example.com/", timeout=20000)
                print("✓ Successfully loaded example.com")
                time.sleep(1)
            except Exception as e:
                print(f"✗ Failed to load example.com: {e}")
            
            # Test Google
            print("\nTesting connection to Google...")
            try:
                start_time = time.time()
                page.goto("https://www.google.com/", timeout=20000)
                load_time = time.time() - start_time
                print(f"✓ Successfully loaded Google in {load_time:.2f} seconds")
                
                # Try to interact with the search box
                try:
                    print("Trying to interact with Google search box...")
                    page.fill('input[name="q"]', 'playwright python')
                    print("✓ Successfully interacted with search box")
                except Exception as e:
                    print(f"✗ Failed to interact with search element: {e}")
            except Exception as e:
                print(f"✗ Failed to load Google: {e}")
            
            # Test Google Trends
            print("\nTesting connection to Google Trends...")
            try:
                start_time = time.time()
                page.goto("https://trends.google.com/trends/explore?geo=CA&q=test", timeout=30000)
                load_time = time.time() - start_time
                print(f"✓ Successfully loaded Google Trends in {load_time:.2f} seconds")
                time.sleep(5)  # Give some time to visually check the page
                
                # Take a screenshot
                screenshot_path = f"{browser_type}_trends_test.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                print(f"✗ Failed to load Google Trends: {e}")
            
            browser.close()
    
    print("\nTest completed")

if __name__ == "__main__":
    run_simple_test() 