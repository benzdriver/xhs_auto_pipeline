#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for enhanced Google Trends data fetching using SerpAPI and PyTrends
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
from utils.logger import get_workflow_logger

# Initialize a logger
logger = get_workflow_logger()

def test_trend_fetching_pipeline():
    """Test the enhanced trend fetching pipeline with SerpAPI and PyTrends"""
    logger.info("=== Testing Enhanced Google Trends Fetching Pipeline ===")
    
    # Set environment variables for testing
    # Set USE_SERPAPI to true to use SerpAPI
    os.environ["USE_SERPAPI"] = "true"
    
    # 关闭代理使用
    os.environ["USE_PROXY"] = "false"
    
    # Check if SERPAPI_KEY is set
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        logger.warning("SERPAPI_KEY environment variable not set")
        logger.warning("Please set it with: export SERPAPI_KEY=your_api_key")
        logger.warning("Will fall back to PyTrends and estimated scores")
    
    # Test with a realistic set of keywords
    test_keywords = [
        "Express Entry",
        "Canadian immigration",
        "Study permit Canada",
        "Work permit Canada",
        "Canada PNP",
        "IRCC processing time",
        "CRS score calculator",
        "Immigration lawyer Canada",
        "Canada PR points",
        "NOC code"
    ]
    
    logger.info(f"Fetching trend scores for {len(test_keywords)} keywords")
    start_time = time.time()
    
    # Get scores using the enhanced batch function
    scores = get_keyword_batch_scores(test_keywords)
    
    duration = time.time() - start_time
    logger.info(f"Completed in {duration:.2f} seconds")
    
    # Display results in order of popularity
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    logger.info("Keywords by popularity:")
    for kw, score in sorted_scores:
        logger.info(f"  {kw}: {score}")
    
    # Save results to file
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"trend_fetch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "results": scores,
            "sorted_results": [{"keyword": kw, "score": score} for kw, score in sorted_scores]
        }, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return scores

if __name__ == "__main__":
    test_trend_fetching_pipeline() 