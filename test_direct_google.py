#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test direct connection to Google without proxies
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the modified fetch_trends module
from stages.fetch_trends import get_trend_score_via_browser, use_fallback_score

def test_direct_connection():
    """Test direct connection to Google Trends without proxies"""
    print("Testing direct connection to Google Trends without proxies")
    
    test_keywords = [
        "Canadian immigration",
        "Express Entry Canada",
    ]
    
    results = {}
    
    for keyword in test_keywords:
        print(f"\nTesting keyword: {keyword}")
        try:
            # Use the modified function with bypass_proxy=True
            score = get_trend_score_via_browser(keyword, bypass_proxy=True)
            print(f"Success! Score: {score}")
            results[keyword] = score
        except Exception as e:
            print(f"Error: {e}")
            results[keyword] = None
        
        # Add a delay between requests
        time.sleep(3)
    
    print("\nTest Results:")
    for keyword, score in results.items():
        print(f"{keyword}: {score}")

if __name__ == "__main__":
    test_direct_connection() 