"""
Integration test for ResponseAnalyzer with PatternDetector.

This tests that the response analyzer correctly integrates with the pattern detector.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.analysis_layer.pattern_detector import PatternDetector
from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


@pytest.fixture
def sample_conversation_df():
    """Create a sample DataFrame with clear response patterns."""
    data = [
        # A conversation with quick responses
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 2), 'phone_number': '5551234567', 'message_type': 'received'},  # 2min
        {'timestamp': datetime(2023, 1, 1, 10, 3), 'phone_number': '5551234567', 'message_type': 'sent'},      # 1min
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},  # 2min
        {'timestamp': datetime(2023, 1, 1, 10, 6), 'phone_number': '5551234567', 'message_type': 'sent'},      # 1min

        # A gap of 3 hours
        
        # A conversation with slow responses
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 15, 0), 'phone_number': '5559876543', 'message_type': 'sent'},      # 60min 
        {'timestamp': datetime(2023, 1, 1, 15, 30), 'phone_number': '5559876543', 'message_type': 'received'}, # 30min
        {'timestamp': datetime(2023, 1, 1, 17, 0), 'phone_number': '5559876543', 'message_type': 'sent'},      # 90min
    ]
    return pd.DataFrame(data)


def test_integration_with_pattern_detector(sample_conversation_df):
    """Test that ResponseAnalyzer integrates correctly with PatternDetector."""
    # Create analyzer and detector
    response_analyzer = ResponseAnalyzer()
    pattern_detector = PatternDetector(response_analyzer=response_analyzer)
    
    # Set up column mapping
    column_mapping = {
        'timestamp': 'timestamp',
        'phone_number': 'phone_number',
        'message_type': 'message_type'
    }
    
    # Run the full pattern detection
    results = pattern_detector.detect_all_patterns(sample_conversation_df, column_mapping)
    
    # Check that the results contain the response analysis
    assert "advanced_analysis" in results
    assert "responses" in results["advanced_analysis"]
    
    # Check that response patterns were converted to the standard format
    response_patterns = [p for p in results["detected_patterns"] 
                         if p.get("pattern_type") in ("response_time", "reciprocity", "conversation_flow")]
    
    # There should be some patterns detected
    assert len(response_patterns) > 0, "No response patterns were detected"
    
    # Check for specific pattern types
    pattern_types = {p.get("subtype", "unknown") for p in response_patterns}
    
    # We should have either quick_responder or delayed_responder pattern
    assert any(subtype in pattern_types for subtype in ("quick_responder", "delayed_responder", "average"))
    
    # There shouldn't be any errors related to response analyzer integration
    response_errors = [e for e in results.get("errors", []) if "ResponseAnalyzer" in e]
    assert len(response_errors) == 0, f"Found response analyzer errors: {response_errors}"


def test_error_handling_in_integration(sample_conversation_df):
    """Test that errors in ResponseAnalyzer are properly handled by PatternDetector."""
    # Create a mock response analyzer that raises an exception
    mock_analyzer = MagicMock(spec=ResponseAnalyzer)
    mock_analyzer.analyze_response_patterns.side_effect = ValueError("Test error")
    
    # Create pattern detector with the mock analyzer
    pattern_detector = PatternDetector(response_analyzer=mock_analyzer)
    
    # Run pattern detection
    results = pattern_detector.detect_all_patterns(sample_conversation_df)
    
    # Check that the error was handled and reported, not raised
    assert "errors" in results
    assert any("ResponseAnalyzer" in str(e) for e in results["errors"])
    
    # The rest of the pattern detection should still have worked
    assert "detected_patterns" in results


if __name__ == "__main__":
    # To run this test file directly
    pytest.main(["-xvs", __file__])
