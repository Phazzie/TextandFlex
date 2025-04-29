"""
Integration test focusing on the _convert_response_results_to_patterns method.

This test verifies that the output from ResponseAnalyzer is correctly converted
to patterns by the PatternDetector.
"""

import unittest
import pandas as pd
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.analysis_layer.pattern_detector import PatternDetector
from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


class TestPatternConversion(unittest.TestCase):
    """Test the _convert_response_results_to_patterns method in PatternDetector."""
    
    def setUp(self):
        """Set up for tests."""
        self.detector = PatternDetector()
    
    def test_convert_response_times(self):
        """Test conversion of response times to patterns."""
        # Create a mock response_times result
        response_results = {
            "response_times": {
                "average_response_time_seconds": 300,  # 5 minutes
                "median_response_time_seconds": 180,   # 3 minutes
                "quick_responders_count": 10,
                "delayed_responders_count": 5,
                "response_time_distribution": {
                    "count": 30,
                    "mean": 300,
                    "std": 150
                }
            }
        }
        
        # Convert to patterns
        patterns = self.detector._convert_response_results_to_patterns(response_results)
        
        # Verify patterns
        self.assertGreater(len(patterns), 0, "Should create at least one pattern")
        
        # Check for average response time pattern
        avg_pattern = next((p for p in patterns if p.get("subtype") == "average"), None)
        self.assertIsNotNone(avg_pattern, "Should create an average response time pattern")
        self.assertEqual(avg_pattern.get("value_seconds"), 300)
        
        # Check for quick responder pattern
        quick_pattern = next((p for p in patterns if p.get("subtype") == "quick_responder"), None)
        self.assertIsNotNone(quick_pattern, "Should create a quick responder pattern")
        
    def test_convert_reciprocity(self):
        """Test conversion of reciprocity patterns."""
        # Create mock reciprocity results with imbalance
        response_results = {
            "reciprocity_patterns": {
                "overall_initiation_ratio": 0.2,  # User rarely initiates
                "contact_reciprocity": {
                    "5551234567": {
                        "sent_messages": 2,
                        "received_messages": 8,
                        "relationship_balance": "mostly_received"
                    }
                }
            }
        }
        
        # Convert to patterns
        patterns = self.detector._convert_response_results_to_patterns(response_results)
        
        # Verify patterns
        self.assertGreater(len(patterns), 0, "Should create at least one pattern")
        
        # Check for initiation imbalance pattern
        imbalance_pattern = next((p for p in patterns if p.get("pattern_type") == "reciprocity"), None)
        self.assertIsNotNone(imbalance_pattern, "Should create a reciprocity pattern")
        self.assertIn("rarely", imbalance_pattern.get("description", ""))
    
    def test_convert_conversation_flows(self):
        """Test conversion of conversation flow patterns."""
        # Create mock conversation flows with long conversations
        response_results = {
            "conversation_flows": {
                "conversation_count": 15,
                "average_duration_seconds": 3600,  # 1 hour
                "average_message_count": 20,
                "common_sequences": [
                    {"sequence": ["sent", "received", "sent"], "count": 10}
                ]
            }
        }
        
        # Convert to patterns
        patterns = self.detector._convert_response_results_to_patterns(response_results)
        
        # Verify patterns
        self.assertGreater(len(patterns), 0, "Should create at least one pattern")
        
        # Check for long conversation pattern
        long_conv_pattern = next((p for p in patterns if p.get("subtype") == "long_conversations"), None)
        self.assertIsNotNone(long_conv_pattern, "Should create a long conversation pattern")
        
        # Check for message intensive pattern
        intensive_pattern = next((p for p in patterns if p.get("subtype") == "message_intensive"), None)
        self.assertIsNotNone(intensive_pattern, "Should create a message intensive pattern")
    
    def test_calculate_significance(self):
        """Test the significance calculation for response times."""
        # Test very fast response (< 1 minute)
        fast_significance = self.detector._calculate_response_time_significance(30)
        self.assertGreater(fast_significance, 1.0, "Fast responses should have high significance")
        
        # Test very slow response (> 1 hour)
        slow_significance = self.detector._calculate_response_time_significance(7200)  # 2 hours
        self.assertGreater(slow_significance, 1.0, "Slow responses should have high significance")
        
        # Test average response (around 10 minutes)
        avg_significance = self.detector._calculate_response_time_significance(600)
        self.assertLessEqual(avg_significance, 1.0, "Average responses should have lower significance")


if __name__ == "__main__":
    unittest.main()
