"""
Comprehensive test suite for ResponseAnalyzer and its integration with PatternDetector.

This file provides tests for:
1. Individual ResponseAnalyzer methods
2. Integration between ResponseAnalyzer and PatternDetector
3. Error handling across components
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the components to test
from src.analysis_layer.pattern_detector import PatternDetector
from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


class TestData:
    """Helper class to create test datasets."""
    
    @staticmethod
    def create_basic_dataset():
        """Create a simple dataset with clear response patterns."""
        data = [
            # A conversation with quick responses
            {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, 1, 10, 2), 'phone_number': '5551234567', 'message_type': 'received'},  # 2min
            {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'sent'},      # 3min
            {'timestamp': datetime(2023, 1, 1, 10, 7), 'phone_number': '5551234567', 'message_type': 'received'},  # 2min

            # A gap of 3 hours
            
            # A conversation with slow responses
            {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
            {'timestamp': datetime(2023, 1, 1, 15, 0), 'phone_number': '5559876543', 'message_type': 'sent'},      # 60min 
            {'timestamp': datetime(2023, 1, 1, 15, 30), 'phone_number': '5559876543', 'message_type': 'received'}, # 30min
            {'timestamp': datetime(2023, 1, 1, 17, 0), 'phone_number': '5559876543', 'message_type': 'sent'},      # 90min
        ]
        return pd.DataFrame(data)
    
    @staticmethod
    def create_edge_case_dataset():
        """Create a dataset with edge cases to test robustness."""
        data = [
            # Empty conversation (just one message)
            {'timestamp': datetime(2023, 1, 1, 8, 0), 'phone_number': '5551111111', 'message_type': 'sent'},
            
            # One-sided conversation (all sent)
            {'timestamp': datetime(2023, 1, 1, 9, 0), 'phone_number': '5552222222', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, 1, 9, 5), 'phone_number': '5552222222', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, 1, 9, 10), 'phone_number': '5552222222', 'message_type': 'sent'},
            
            # One-sided conversation (all received)
            {'timestamp': datetime(2023, 1, 1, 11, 0), 'phone_number': '5553333333', 'message_type': 'received'},
            {'timestamp': datetime(2023, 1, 1, 11, 5), 'phone_number': '5553333333', 'message_type': 'received'},
            {'timestamp': datetime(2023, 1, 1, 11, 10), 'phone_number': '5553333333', 'message_type': 'received'},
            
            # Mixed conversation with simultaneous timestamps
            {'timestamp': datetime(2023, 1, 1, 13, 0), 'phone_number': '5554444444', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, 1, 13, 0), 'phone_number': '5554444444', 'message_type': 'received'},
            {'timestamp': datetime(2023, 1, 1, 13, 5), 'phone_number': '5554444444', 'message_type': 'sent'},
            {'timestamp': datetime(2023, 1, 1, 13, 5), 'phone_number': '5554444444', 'message_type': 'received'},
        ]
        return pd.DataFrame(data)


class TestResponseAnalyzer(unittest.TestCase):
    """Test the ResponseAnalyzer component."""
    
    def setUp(self):
        """Set up the test environment."""
        self.analyzer = ResponseAnalyzer()
        self.basic_df = TestData.create_basic_dataset()
        self.edge_df = TestData.create_edge_case_dataset()
    
    def test_analyze_response_times(self):
        """Test that _calculate_response_times works correctly."""
        # Test with basic dataset
        result = self.analyzer._calculate_response_times(self.basic_df, {
            'timestamp': 'timestamp',
            'phone_number': 'phone_number',
            'message_type': 'message_type'
        })
        
        # Verify structure
        self.assertIn('average_response_time_seconds', result)
        self.assertIn('median_response_time_seconds', result)
        self.assertIn('response_time_distribution', result)
        
        # Verify averages make sense for our data
        avg_time = result['average_response_time_seconds']
        if avg_time is not None:
            self.assertGreater(avg_time, 0)  # Should be positive
        
        # Check that details DataFrame exists
        self.assertIn('details', result)
    
    def test_analyze_reciprocity(self):
        """Test that _analyze_reciprocity works correctly."""
        # Test with basic dataset
        result = self.analyzer._analyze_reciprocity(self.basic_df, {
            'timestamp': 'timestamp',
            'phone_number': 'phone_number',
            'message_type': 'message_type'
        })
        
        # Verify structure
        self.assertIn('overall_initiation_ratio', result)
        self.assertIn('contact_reciprocity', result)
        
        # Check individual contacts
        self.assertGreaterEqual(len(result['contact_reciprocity']), 2)  # Should have at least 2 contacts
    
    def test_analyze_conversation_flows(self):
        """Test that _analyze_conversation_flows works correctly."""
        # Test with basic dataset
        result = self.analyzer._analyze_conversation_flows(self.basic_df, {
            'timestamp': 'timestamp',
            'phone_number': 'phone_number',
            'message_type': 'message_type'
        })
        
        # Verify structure
        self.assertIn('conversation_count', result)
        self.assertIn('average_duration_seconds', result)
        self.assertIn('common_sequences', result)
        
        # Should identify at least 2 conversations
        self.assertGreaterEqual(result['conversation_count'], 2)
    
    def test_empty_dataset(self):
        """Test behavior with empty dataset."""
        empty_df = pd.DataFrame()
        result = self.analyzer.analyze_response_patterns(empty_df, None)
        
        # Should return an error
        self.assertIn('error', result)
        self.assertIsNotNone(result['error'])
    
    def test_edge_cases(self):
        """Test behavior with edge case dataset."""
        result = self.analyzer.analyze_response_patterns(self.edge_df, None)
        
        # Should not error
        self.assertTrue('error' not in result or result['error'] is None)
        
        # Check for one-sided conversations
        reciprocity = result.get('reciprocity_patterns', {})
        if reciprocity:
            contacts = reciprocity.get('contact_reciprocity', {})
            # Look for one-sided relationship balance
            one_sided_found = False
            for contact_id, metrics in contacts.items():
                if metrics.get('relationship_balance') in ['only_sent', 'only_received']:
                    one_sided_found = True
                    break
            self.assertTrue(one_sided_found)


class TestIntegration(unittest.TestCase):
    """Test the integration between ResponseAnalyzer and PatternDetector."""
    
    def setUp(self):
        """Set up the test environment."""
        self.analyzer = ResponseAnalyzer()
        self.detector = PatternDetector(response_analyzer=self.analyzer)
        self.basic_df = TestData.create_basic_dataset()
    
    def test_integration_basic(self):
        """Test basic integration between components."""
        results = self.detector.detect_all_patterns(self.basic_df, {
            'timestamp': 'timestamp',
            'phone_number': 'phone_number',
            'message_type': 'message_type'
        })
        
        # Check that we have results from advanced analysis
        self.assertIn('advanced_analysis', results)
        self.assertIn('responses', results['advanced_analysis'])
        
        # Check that response patterns were converted
        response_patterns = [p for p in results['detected_patterns'] 
                            if p.get('pattern_type') in ('response_time', 'reciprocity', 'conversation_flow')]
        self.assertGreater(len(response_patterns), 0)
        
        # Check for specific pattern types
        pattern_subtypes = [p.get('subtype') for p in response_patterns]
        self.assertTrue(any(subtype in pattern_subtypes for subtype in 
                           ['average', 'quick_responder', 'delayed_responder']))
    
    def test_integration_error_handling(self):
        """Test error handling in the integration."""
        # Create a mock analyzer that raises an exception
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_response_patterns.side_effect = ValueError("Test error")
        
        # Create detector with mock analyzer
        detector = PatternDetector(response_analyzer=mock_analyzer)
        
        # Run pattern detection
        results = detector.detect_all_patterns(self.basic_df)
        
        # Check that the error was handled, not propagated
        self.assertIn('errors', results)
        self.assertTrue(any('ResponseAnalyzer' in str(e) for e in results['errors']))
        
        # The detector should still return results
        self.assertIn('detected_patterns', results)
    
    def test_conversion_to_patterns(self):
        """Test the conversion of response results to pattern format."""
        # First get raw results from analyzer
        analyzer_results = self.analyzer.analyze_response_patterns(self.basic_df, None)
        
        # Then manually convert using the detector method
        patterns = self.detector._convert_response_results_to_patterns(analyzer_results)
        
        # Check that we got some patterns
        self.assertGreater(len(patterns), 0)
        
        # Check pattern structure
        for pattern in patterns:
            self.assertIn('pattern_type', pattern)
            self.assertIn('subtype', pattern)
            self.assertIn('description', pattern)
            self.assertIn('significance', pattern)


def run_tests():
    """Run all tests and print results."""
    print("\n=== Running ResponseAnalyzer and Integration Tests ===\n")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestResponseAnalyzer))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Ran {result.testsRun} tests")
    print(f"Success: {result.wasSuccessful()}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for i, (test, error) in enumerate(result.errors):
            print(f"Error {i+1}: {test}")
            print(error)
    if result.failures:
        print(f"Failures: {len(result.failures)}")
        for i, (test, failure) in enumerate(result.failures):
            print(f"Failure {i+1}: {test}")
            print(failure)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
