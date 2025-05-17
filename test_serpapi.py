#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Google Trends data fetching via SerpAPI and PyTrends
"""

import os
import sys
import json
import time
from datetime import datetime

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the functions
from stages.fetch_trends import get_trend_score_via_serpapi, get_keyword_batch_scores
from pytrends.request import TrendReq

def test_methods():
    """Test Google Trends data fetching via SerpAPI and PyTrends"""
    print("Testing Google Trends data fetching methods")
    
    # Check if SERPAPI_KEY is set
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("WARNING: SERPAPI_KEY environment variable not set")
        print("SerpAPI tests will be skipped")
        print("Please set it with: export SERPAPI_KEY=your_api_key")
    else:
        print("SerpAPI key detected, will test SerpAPI method")
        
    # Enable SerpAPI for testing
    if api_key:
        os.environ["USE_SERPAPI"] = "true"
    
    # Test keywords
    test_keywords = [
        "Canadian immigration",
        "Express Entry Canada",
        "Canada PNP",
        "Study permit Canada"
    ]
    
    # Test using batch function (tests both SerpAPI and PyTrends fallback)
    print("\n=== Testing Batch Processing ===")
    start_time = time.time()
    batch_results = get_keyword_batch_scores(test_keywords)
    batch_time = time.time() - start_time
    print(f"Batch processing completed in {batch_time:.2f} seconds")
    
    # Test using SerpAPI directly if key is available
    serpapi_results = {}
    if api_key:
        print("\n=== Testing SerpAPI directly ===")
        for keyword in test_keywords:
            print(f"\nFetching trend score for: {keyword}")
            try:
                start_time = time.time()
                score = get_trend_score_via_serpapi(keyword)
                fetch_time = time.time() - start_time
                print(f"Success! Score: {score} (took {fetch_time:.2f}s)")
                serpapi_results[keyword] = score
            except Exception as e:
                print(f"Error: {e}")
                serpapi_results[keyword] = None
            
            # Add a delay between requests to respect API limits
            time.sleep(2)
    
    # Test using PyTrends directly
    pytrends_results = {}
    print("\n=== Testing PyTrends directly ===")
    try:
        pytrends = TrendReq(hl='en-CA', tz=360)
        for keyword in test_keywords:
            print(f"\nFetching trend score for: {keyword} via PyTrends")
            try:
                start_time = time.time()
                pytrends.build_payload([keyword], timeframe="now 7-d", geo="CA")
                data = pytrends.interest_over_time()
                if not data.empty and keyword in data:
                    score = int(data[keyword].mean())
                    fetch_time = time.time() - start_time
                    print(f"Success! Score: {score} (took {fetch_time:.2f}s)")
                    pytrends_results[keyword] = score
                else:
                    print("PyTrends returned empty data")
                    pytrends_results[keyword] = None
            except Exception as e:
                print(f"Error: {e}")
                pytrends_results[keyword] = None
            
            # Add a delay between requests to respect API limits
            time.sleep(2)
    except Exception as e:
        print(f"Error initializing PyTrends: {e}")
    
    # Save results to file
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "trends_method_comparison.json")
    
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "batch_results": batch_results,
            "serpapi_results": serpapi_results,
            "pytrends_results": pytrends_results
        }, f, indent=2)
    
    print(f"\nTest results saved to {output_file}")
    print("\n=== Summary ===")
    print("Batch processing results:")
    for keyword, score in batch_results.items():
        print(f"  {keyword}: {score}")
        
    if api_key:
        print("\nSerpAPI direct results:")
        for keyword, score in serpapi_results.items():
            print(f"  {keyword}: {score}")
            
    print("\nPyTrends direct results:")
    for keyword, score in pytrends_results.items():
        print(f"  {keyword}: {score}")

if __name__ == "__main__":
    test_methods() 