"""
Test script for ResponseAnalyzer and PatternDetector integration.

Usage: python integration_test.py
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import sys
import os
from pprint import pprint

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis_layer.pattern_detector import PatternDetector
from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


def create_sample_data():
    """Create a realistic sample dataset for testing."""
    now = datetime.now()
    hours_ago = lambda h: now - timedelta(hours=h)
    
    data = [
        # Conversation 1: Quick responder
        {'timestamp': hours_ago(24), 'phone_number': '555-1111', 'message_type': 'received'},
        {'timestamp': hours_ago(23.95), 'phone_number': '555-1111', 'message_type': 'sent'},     # 3min
        {'timestamp': hours_ago(23.9), 'phone_number': '555-1111', 'message_type': 'received'},  # 3min
        {'timestamp': hours_ago(23.85), 'phone_number': '555-1111', 'message_type': 'sent'},     # 3min
        
        # Conversation 2: Delayed responder
        {'timestamp': hours_ago(20), 'phone_number': '555-2222', 'message_type': 'received'},
        {'timestamp': hours_ago(19), 'phone_number': '555-2222', 'message_type': 'sent'},        # 60min
        {'timestamp': hours_ago(18), 'phone_number': '555-2222', 'message_type': 'received'},
        {'timestamp': hours_ago(17), 'phone_number': '555-2222', 'message_type': 'sent'},        # 60min
        
        # Conversation 3: Mixed response times
        {'timestamp': hours_ago(12), 'phone_number': '555-3333', 'message_type': 'sent'},
        {'timestamp': hours_ago(11.9), 'phone_number': '555-3333', 'message_type': 'received'},  # 6min
        {'timestamp': hours_ago(10), 'phone_number': '555-3333', 'message_type': 'sent'},        # 114min
        {'timestamp': hours_ago(9.9), 'phone_number': '555-3333', 'message_type': 'received'},   # 6min
        
        # Conversation 4: One-sided (only sent)
        {'timestamp': hours_ago(6), 'phone_number': '555-4444', 'message_type': 'sent'},
        {'timestamp': hours_ago(5), 'phone_number': '555-4444', 'message_type': 'sent'},
        {'timestamp': hours_ago(4), 'phone_number': '555-4444', 'message_type': 'sent'},
        
        # Conversation 5: One-sided (only received)
        {'timestamp': hours_ago(3), 'phone_number': '555-5555', 'message_type': 'received'},
        {'timestamp': hours_ago(2), 'phone_number': '555-5555', 'message_type': 'received'},
        {'timestamp': hours_ago(1), 'phone_number': '555-5555', 'message_type': 'received'},
    ]
    
    return pd.DataFrame(data)


def format_results_for_display(results):
    """Format complex objects in results for display."""
    formatted = results.copy()
    
    # Handle DataFrames
    if "advanced_analysis" in formatted and "responses" in formatted["advanced_analysis"]:
        responses = formatted["advanced_analysis"]["responses"]
        
        # Convert any DataFrames to summary counts
        for section in ["response_times", "reciprocity_patterns", "conversation_flows"]:
            if section in responses and responses[section] and "details" in responses[section]:
                details = responses[section]["details"]
                if hasattr(details, "shape"):  # It's a DataFrame
                    responses[section]["details"] = f"<DataFrame: {details.shape[0]} rows, {details.shape[1]} columns>"
    
    return formatted


def run_integration_test():
    """Run the integration test and display results."""
    print("Creating sample data...")
    df = create_sample_data()
    print(f"Created DataFrame with {len(df)} records.")
    
    print("\nInitializing ResponseAnalyzer and PatternDetector...")
    response_analyzer = ResponseAnalyzer()
    pattern_detector = PatternDetector(response_analyzer=response_analyzer)
    
    print("\nRunning analyze_response_patterns directly...")
    response_results = response_analyzer.analyze_response_patterns(df, None)
    print("Response analyzer returned:")
    for key in response_results:
        if key == "error" and response_results[key] is None:
            continue
        print(f"  - {key}: {'<data>' if response_results[key] else 'None'}")
    
    print("\nRunning PatternDetector.detect_all_patterns...")
    detector_results = pattern_detector.detect_all_patterns(df)
    
    # Get response patterns that were converted
    response_patterns = [p for p in detector_results["detected_patterns"] 
                        if p.get("pattern_type") in ("response_time", "reciprocity", "conversation_flow")]
    
    print(f"\nPatternDetector found {len(response_patterns)} response patterns:")
    for i, pattern in enumerate(response_patterns):
        print(f"  {i+1}. [{pattern.get('pattern_type')}] {pattern.get('description')}")
    
    print("\nDetailed response_patterns:")
    pprint(response_patterns)
    
    # Check for errors
    if detector_results.get("errors"):
        print("\nErrors detected:")
        for error in detector_results["errors"]:
            print(f"  - {error}")
    else:
        print("\nNo errors detected.")
    
    return {
        "response_results": response_results,
        "detector_results": detector_results
    }


if __name__ == "__main__":
    run_integration_test()
