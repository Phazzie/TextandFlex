"""
Simple script to run the ResponseAnalyzer integration test directly.
"""

# Standard library imports
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union, Optional, Tuple, cast

# Third-party imports
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.analysis_layer.pattern_detector import PatternDetector
    from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer
except ImportError as e:
    with open('import_error.txt', 'w') as f:
        f.write(f"Error importing modules: {str(e)}\n")
        f.write(f"sys.path: {sys.path}")
    sys.exit(1)

def create_test_data() -> pd.DataFrame:
    """Create a simple test dataset with response patterns."""
    data = [
        # Quick responses
        {'timestamp': datetime(2023, 1, 1, 10, 0), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 2), 'phone_number': '5551234567', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 10, 5), 'phone_number': '5551234567', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 10, 7), 'phone_number': '5551234567', 'message_type': 'sent'},

        # Slow responses
        {'timestamp': datetime(2023, 1, 1, 14, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 15, 0), 'phone_number': '5559876543', 'message_type': 'sent'},
        {'timestamp': datetime(2023, 1, 1, 16, 0), 'phone_number': '5559876543', 'message_type': 'received'},
        {'timestamp': datetime(2023, 1, 1, 17, 30), 'phone_number': '5559876543', 'message_type': 'sent'},
    ]
    return pd.DataFrame(data)

def run_integration_test() -> bool:
    """Run the integration test between ResponseAnalyzer and PatternDetector.

    Returns:
        bool: True if the test passed, False otherwise
    """
    output: List[str] = []
    output.extend([
        "\n=== Running ResponseAnalyzer Integration Test ===\n",
        "Creating test data..."
    ])
    df = create_test_data()
    output.append(f"Created dataset with {len(df)} records")

    # Initialize components
    output.append("\nInitializing ResponseAnalyzer and PatternDetector...")
    analyzer = ResponseAnalyzer()
    detector = PatternDetector(response_analyzer=analyzer)
    # Run analyzer directly
    output.append("\nRunning ResponseAnalyzer.analyze_response_patterns() directly...")
    response_results = analyzer.analyze_response_patterns(df, None)

    if response_results.get("error"):
        output.append(f"ERROR: ResponseAnalyzer returned an error: {response_results['error']}")
    else:
        output.append("SUCCESS: ResponseAnalyzer ran without errors")
        # Print response times
        if rt := response_results.get("response_times"):
            output.extend([
                f"Avg response time: {rt.get('average_response_time_seconds')} seconds",
                f"Quick responders: {rt.get('quick_responders_count')}",
                f"Delayed responders: {rt.get('delayed_responders_count')}"
            ])

    # Run pattern detector
    output.append("\nRunning PatternDetector.detect_all_patterns()...")
    detector_results = detector.detect_all_patterns(df, None)

    has_analyzer_errors = (
        "errors" in detector_results and
        any("ResponseAnalyzer" in str(e) for e in detector_results["errors"])
    )

    if has_analyzer_errors:
        output.append(f"ERROR: PatternDetector had errors with ResponseAnalyzer: {detector_results['errors']}")
    else:
        output.append("SUCCESS: PatternDetector integrated with ResponseAnalyzer without errors")

        # Check converted patterns
        response_patterns = [
            p for p in detector_results.get("detected_patterns", [])
            if p.get("pattern_type") in ("response_time", "reciprocity", "conversation_flow")
        ]

        output.append(f"\nFound {len(response_patterns)} response patterns in results:")
        for i, pattern in enumerate(response_patterns):
            output.append(f"{i+1}. [{pattern.get('pattern_type')}] {pattern.get('subtype')}: {pattern.get('description')}")
    output.append("\n=== Integration Test Complete ===")

    # Write output to file
    results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'integration_test_results.txt')
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
      # Return success status: True if no ResponseAnalyzer-related errors were found
    return not has_analyzer_errors

if __name__ == "__main__":
    try:
        success = run_integration_test()
          # Write success or failure status
        status_file = 'test_success.txt' if success else 'test_failure.txt'
        status_message = "Integration test " + ("succeeded" if success else "failed") + ". See integration_test_results.txt for details."
        with open(status_file, 'w') as f:
            f.write(status_message)

        print("Integration test " + ("succeeded" if success else "failed") + ".")
        print("Results written to integration_test_results.txt")

    except Exception as e:
        import traceback
        error_message = f"Error during integration test: {str(e)}\n\n{traceback.format_exc()}"

        with open('test_error.txt', 'w') as f:
            f.write(error_message)

        print(f"ERROR: {str(e)}")
        print("Full error details written to test_error.txt")

        # Re-raise for traceback
        raise
