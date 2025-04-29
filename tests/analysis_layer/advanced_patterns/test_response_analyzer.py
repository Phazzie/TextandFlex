"""
Tests for the ResponseAnalyzer component.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Import the ResponseAnalyzer class
from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


class TestResponseAnalyzer(unittest.TestCase):
    """Test cases for the ResponseAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock logger
        self.mock_logger = MagicMock()
        
        # Create a mock config
        self.mock_config = MagicMock()
        self.mock_config.get.return_value = 1.0  # Default value for config parameters
        
        # Create a mock ML model service
        self.mock_ml_service = MagicMock()
        
        # Create the ResponseAnalyzer instance
        self.analyzer = ResponseAnalyzer(
            ml_model_service=self.mock_ml_service,
            config=self.mock_config,
            logger_instance=self.mock_logger
        )
        
        # Create sample data for testing
        self.create_sample_data()
        
    def create_sample_data(self):
        """Create sample data for testing."""
        # Create a DataFrame with sample data
        self.sample_data = pd.DataFrame({
            'timestamp': [
                # Conversation 1 with Contact A
                datetime(2023, 1, 1, 10, 0),  # User sends message
                datetime(2023, 1, 1, 10, 5),  # Contact A responds (5 min)
                datetime(2023, 1, 1, 10, 10), # User responds (5 min)
                datetime(2023, 1, 1, 10, 20), # Contact A responds (10 min)
                
                # Conversation 2 with Contact B
                datetime(2023, 1, 1, 14, 0),  # Contact B initiates
                datetime(2023, 1, 1, 14, 30), # User responds (30 min)
                datetime(2023, 1, 1, 15, 0),  # Contact B responds (30 min)
                datetime(2023, 1, 1, 16, 0),  # User responds (60 min)
                
                # Conversation 3 with Contact C
                datetime(2023, 1, 2, 9, 0),   # User initiates
                datetime(2023, 1, 2, 9, 45),  # Contact C responds (45 min)
                datetime(2023, 1, 2, 10, 0),  # User responds (15 min)
                datetime(2023, 1, 2, 10, 3),  # Contact C responds (3 min)
            ],
            'phone_number': [
                'Contact A', 'Contact A', 'Contact A', 'Contact A',
                'Contact B', 'Contact B', 'Contact B', 'Contact B',
                'Contact C', 'Contact C', 'Contact C', 'Contact C'
            ],
            'message_type': [
                'sent', 'received', 'sent', 'received',
                'received', 'sent', 'received', 'sent',
                'sent', 'received', 'sent', 'received'
            ]
        })
        
        # Create column mapping
        self.column_mapping = {
            'timestamp': 'timestamp',
            'phone_number': 'phone_number',
            'message_type': 'message_type'
        }
        
        # Create empty data for testing edge cases
        self.empty_data = pd.DataFrame(columns=['timestamp', 'phone_number', 'message_type'])
        
        # Create data with missing columns
        self.missing_column_data = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 1, 10, 0)],
            'phone_number': ['Contact A']
            # Missing 'message_type'
        })
        
        # Create data with invalid timestamp format
        self.invalid_timestamp_data = pd.DataFrame({
            'timestamp': ['not-a-date'],
            'phone_number': ['Contact A'],
            'message_type': ['sent']
        })
        
        # Create data with only sent messages (no responses)
        self.only_sent_data = pd.DataFrame({
            'timestamp': [
                datetime(2023, 1, 1, 10, 0),
                datetime(2023, 1, 1, 11, 0),
                datetime(2023, 1, 1, 12, 0)
            ],
            'phone_number': ['Contact A', 'Contact B', 'Contact C'],
            'message_type': ['sent', 'sent', 'sent']
        })
        
        # Create data with only received messages (no responses)
        self.only_received_data = pd.DataFrame({
            'timestamp': [
                datetime(2023, 1, 1, 10, 0),
                datetime(2023, 1, 1, 11, 0),
                datetime(2023, 1, 1, 12, 0)
            ],
            'phone_number': ['Contact A', 'Contact B', 'Contact C'],
            'message_type': ['received', 'received', 'received']
        })
        
        # Create data with outlier response times
        self.outlier_data = pd.DataFrame({
            'timestamp': [
                datetime(2023, 1, 1, 10, 0),  # User sends message
                datetime(2023, 1, 1, 10, 5),  # Contact A responds (5 min)
                datetime(2023, 1, 1, 12, 0),  # User sends message
                datetime(2023, 1, 1, 18, 0),  # Contact A responds (6 hours - outlier)
            ],
            'phone_number': ['Contact A', 'Contact A', 'Contact A', 'Contact A'],
            'message_type': ['sent', 'received', 'sent', 'received']
        })

    def test_init(self):
        """Test the constructor."""
        # Test with default parameters
        analyzer = ResponseAnalyzer()
        self.assertIsNone(analyzer.ml_model_service)
        self.assertIsNone(analyzer.config)
        self.assertIsNotNone(analyzer.logger)
        self.assertIsNone(analyzer.last_error)
        
        # Test with custom parameters
        analyzer = ResponseAnalyzer(
            ml_model_service=self.mock_ml_service,
            config=self.mock_config,
            logger_instance=self.mock_logger
        )
        self.assertEqual(analyzer.ml_model_service, self.mock_ml_service)
        self.assertEqual(analyzer.config, self.mock_config)
        self.assertEqual(analyzer.logger, self.mock_logger)
        self.assertIsNone(analyzer.last_error)

    def test_analyze_response_patterns_with_valid_data(self):
        """Test analyze_response_patterns with valid data."""
        # Call the method
        results = self.analyzer.analyze_response_patterns(self.sample_data, self.column_mapping)
        
        # Check that the results have the expected structure
        self.assertIn('response_times', results)
        self.assertIn('reciprocity_patterns', results)
        self.assertIn('conversation_flows', results)
        self.assertIn('anomalies', results)
        self.assertNotIn('error', results)
        
        # Check response times
        response_times = results['response_times']
        self.assertIsNotNone(response_times.get('average_response_time_seconds'))
        self.assertIsNotNone(response_times.get('median_response_time_seconds'))
        self.assertIsNotNone(response_times.get('response_time_distribution'))
        
        # Check reciprocity patterns
        reciprocity = results['reciprocity_patterns']
        self.assertIsNotNone(reciprocity.get('overall_initiation_ratio'))
        self.assertIsNotNone(reciprocity.get('contact_reciprocity'))
        
        # Check conversation flows
        flows = results['conversation_flows']
        self.assertIsNotNone(flows.get('conversation_count'))
        self.assertIsNotNone(flows.get('average_duration_seconds'))
        
        # Check that the ML service was not called (since we're not testing that here)
        self.mock_ml_service.predict.assert_not_called()

    def test_analyze_response_patterns_with_empty_data(self):
        """Test analyze_response_patterns with empty data."""
        # Call the method
        results = self.analyzer.analyze_response_patterns(self.empty_data, self.column_mapping)
        
        # Check that an error is returned
        self.assertIn('error', results)
        self.assertEqual(results['error'], "Input DataFrame is empty.")
        
        # Check that the last_error attribute is set
        self.assertEqual(self.analyzer.last_error, "Input DataFrame is empty.")
        
        # Check that the logger was called with an error message
        self.mock_logger.error.assert_called_with("Input DataFrame is empty.")

    def test_analyze_response_patterns_with_missing_columns(self):
        """Test analyze_response_patterns with missing columns."""
        # Call the method
        results = self.analyzer.analyze_response_patterns(self.missing_column_data, self.column_mapping)
        
        # Check that an error is returned
        self.assertIn('error', results)
        self.assertTrue("missing required mapped columns" in results['error'])
        
        # Check that the last_error attribute is set
        self.assertTrue("missing required mapped columns" in self.analyzer.last_error)
        
        # Check that the logger was called with an error message
        self.mock_logger.error.assert_called()

    def test_calculate_response_times(self):
        """Test _calculate_response_times method."""
        # Call the method
        results = self.analyzer._calculate_response_times(self.sample_data, self.column_mapping)
        
        # Check that the results have the expected structure
        self.assertIn('average_response_time_seconds', results)
        self.assertIn('median_response_time_seconds', results)
        self.assertIn('response_time_distribution', results)
        self.assertIn('per_contact_average', results)
        self.assertIn('by_hour_average', results)
        self.assertIn('by_day_average', results)
        self.assertIn('quick_responders_count', results)
        self.assertIn('delayed_responders_count', results)
        self.assertIn('outliers', results)
        
        # Check that the average response time is calculated correctly
        # In our sample data, we have response times of 5, 10, 30, 30, 45, 3 minutes
        # Average should be (5*60 + 10*60 + 30*60 + 30*60 + 45*60 + 3*60) / 6 = 1230 seconds
        expected_avg = (5*60 + 10*60 + 30*60 + 30*60 + 45*60 + 3*60) / 6
        self.assertAlmostEqual(results['average_response_time_seconds'], expected_avg, delta=1)
        
        # Check that per-contact averages are calculated
        self.assertIn('Contact A', results['per_contact_average'])
        self.assertIn('Contact B', results['per_contact_average'])
        self.assertIn('Contact C', results['per_contact_average'])
        
        # Check Contact A's average (5 and 10 minutes)
        expected_contact_a_avg = (5*60 + 10*60) / 2
        self.assertAlmostEqual(results['per_contact_average']['Contact A'], expected_contact_a_avg, delta=1)

    def test_calculate_response_times_with_no_responses(self):
        """Test _calculate_response_times with no response pairs."""
        # Call the method with only sent messages
        results = self.analyzer._calculate_response_times(self.only_sent_data, self.column_mapping)
        
        # Check that appropriate default values are returned
        self.assertIsNone(results['average_response_time_seconds'])
        self.assertIsNone(results['median_response_time_seconds'])
        self.assertEqual(results['quick_responders_count'], 0)
        self.assertEqual(results['delayed_responders_count'], 0)
        self.assertEqual(len(results['outliers']), 0)
        
        # Check that the logger was called with a warning
        self.mock_logger.warning.assert_called_with("No response pairs found to calculate response times.")

    def test_analyze_reciprocity(self):
        """Test _analyze_reciprocity method."""
        # Call the method
        results = self.analyzer._analyze_reciprocity(self.sample_data, self.column_mapping)
        
        # Check that the results have the expected structure
        self.assertIn('overall_initiation_ratio', results)
        self.assertIn('contact_reciprocity', results)
        self.assertIn('details', results)
        
        # Check that the overall initiation ratio is calculated correctly
        # In our sample data, we have 2 user-initiated conversations out of 3 total
        expected_ratio = 2/3
        self.assertAlmostEqual(results['overall_initiation_ratio'], expected_ratio, delta=0.01)
        
        # Check that contact reciprocity data is calculated
        self.assertIn('Contact A', results['contact_reciprocity'])
        self.assertIn('Contact B', results['contact_reciprocity'])
        self.assertIn('Contact C', results['contact_reciprocity'])
        
        # Check that message counts are correct
        contact_a_data = results['contact_reciprocity']['Contact A']
        self.assertEqual(contact_a_data['sent_messages'], 2)
        self.assertEqual(contact_a_data['received_messages'], 2)
        
        # Check relationship balance categorization
        # All contacts have balanced communication (2 sent, 2 received)
        self.assertEqual(contact_a_data['relationship_balance'], 'balanced')

    def test_analyze_conversation_flows(self):
        """Test _analyze_conversation_flows method."""
        # Call the method
        results = self.analyzer._analyze_conversation_flows(self.sample_data, self.column_mapping)
        
        # Check that the results have the expected structure
        self.assertIn('conversation_count', results)
        self.assertIn('average_duration_seconds', results)
        self.assertIn('average_message_count', results)
        self.assertIn('distribution_by_hour', results)
        self.assertIn('distribution_by_day', results)
        self.assertIn('details', results)
        
        # Check that the conversation count is correct
        # In our sample data, we have 3 distinct conversations
        self.assertEqual(results['conversation_count'], 3)
        
        # Check that the average message count is correct
        # Each conversation has 4 messages
        self.assertEqual(results['average_message_count'], 4)
        
        # Check conversation details
        details_df = results['details']
        self.assertEqual(len(details_df), 3)  # 3 conversations
        
        # Check initiator types
        initiator_types = details_df['initiator_type'].tolist()
        # Conversation 1: User initiated (sent)
        # Conversation 2: Contact initiated (received)
        # Conversation 3: User initiated (sent)
        expected_initiator_types = ['sent', 'received', 'sent']
        self.assertEqual(initiator_types, expected_initiator_types)

    def test_detect_response_anomalies(self):
        """Test _detect_response_anomalies method."""
        # First, get analysis results for data with outliers
        analysis_results = {
            'response_times': self.analyzer._calculate_response_times(self.outlier_data, self.column_mapping),
            'reciprocity_patterns': self.analyzer._analyze_reciprocity(self.outlier_data, self.column_mapping),
            'conversation_flows': self.analyzer._analyze_conversation_flows(self.outlier_data, self.column_mapping)
        }
        
        # Call the method
        anomalies = self.analyzer._detect_response_anomalies(self.column_mapping, analysis_results)
        
        # Check that anomalies are detected
        self.assertGreater(len(anomalies), 0)
        
        # Check that the anomalies have the expected structure
        for anomaly in anomalies:
            self.assertIn('type', anomaly)
            self.assertIn('description', anomaly)
            self.assertIn('severity', anomaly)
            self.assertIn('contact', anomaly)
            self.assertIn('details', anomaly)
            
            # Check that severity is between 0 and 1
            self.assertGreaterEqual(anomaly['severity'], 0)
            self.assertLessEqual(anomaly['severity'], 1)

    def test_caching(self):
        """Test that results are cached and reused."""
        # Mock the cache functions
        with patch('src.analysis_layer.advanced_patterns.response_analyzer.get_cached_result') as mock_get_cache, \
             patch('src.analysis_layer.advanced_patterns.response_analyzer.cache_result') as mock_cache_result:
            
            # First call - no cached result
            mock_get_cache.return_value = None
            
            # Call the method
            self.analyzer.analyze_response_patterns(self.sample_data, self.column_mapping)
            
            # Check that get_cached_result was called
            mock_get_cache.assert_called_once()
            
            # Check that cache_result was called
            mock_cache_result.assert_called_once()
            
            # Reset mocks
            mock_get_cache.reset_mock()
            mock_cache_result.reset_mock()
            
            # Second call - cached result exists
            mock_get_cache.return_value = {'cached': True}
            
            # Call the method again
            result = self.analyzer.analyze_response_patterns(self.sample_data, self.column_mapping)
            
            # Check that get_cached_result was called
            mock_get_cache.assert_called_once()
            
            # Check that cache_result was NOT called
            mock_cache_result.assert_not_called()
            
            # Check that the cached result was returned
            self.assertEqual(result, {'cached': True})


if __name__ == '__main__':
    unittest.main()
