"""
Performance tests for the ResponseAnalyzer component.

This module contains tests for the performance of the ResponseAnalyzer with large datasets.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import gc
import psutil
import os
from unittest.mock import MagicMock, patch

from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer


@pytest.fixture
def large_dataset():
    """Create a large dataset for performance testing (10,000+ records)."""
    data = []
    
    # Generate data for 10 contacts over 100 days (10,000+ records)
    contacts = [f"555{i:07d}" for i in range(10)]
    
    for day in range(1, 101):  # 100 days
        for hour in range(8, 20):  # 12 hours per day
            for contact in contacts:
                # Add sent message
                data.append({
                    'timestamp': datetime(2023, 1, day, hour, 0),
                    'phone_number': contact,
                    'message_type': 'sent'
                })
                
                # Add received message with random response time (1-30 minutes)
                response_minutes = np.random.randint(1, 31)
                data.append({
                    'timestamp': datetime(2023, 1, day, hour, response_minutes),
                    'phone_number': contact,
                    'message_type': 'received'
                })
    
    return pd.DataFrame(data)


def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


@pytest.mark.performance
def test_large_dataset_performance(large_dataset):
    """Test performance with a large dataset (10,000+ records)."""
    analyzer = ResponseAnalyzer()
    
    # Measure initial memory usage
    initial_memory = get_memory_usage()
    
    # Measure execution time
    start_time = time.time()
    result = analyzer.analyze_response_patterns(large_dataset)
    execution_time = time.time() - start_time
    
    # Measure final memory usage
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    # Log performance metrics
    print(f"\nPerformance metrics:")
    print(f"Dataset size: {len(large_dataset)} records")
    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Memory increase: {memory_increase:.2f} MB")
    
    # Check that the analysis completed successfully
    assert isinstance(result, dict)
    assert 'conversation_flows' in result
    assert 'response_times' in result
    assert 'reciprocity_patterns' in result
    
    # Check performance requirements
    assert execution_time < 60  # Should complete in less than 60 seconds
    assert memory_increase < 1000  # Should use less than 1000 MB additional memory


@pytest.mark.performance
def test_caching_mechanism(large_dataset):
    """Test that caching improves performance on repeated calls."""
    analyzer = ResponseAnalyzer()
    
    # First call (no cache)
    start_time_first = time.time()
    result_first = analyzer.analyze_response_patterns(large_dataset)
    execution_time_first = time.time() - start_time_first
    
    # Force garbage collection to ensure fair comparison
    gc.collect()
    
    # Second call (should use cache)
    start_time_second = time.time()
    result_second = analyzer.analyze_response_patterns(large_dataset)
    execution_time_second = time.time() - start_time_second
    
    # Log performance metrics
    print(f"\nCaching performance metrics:")
    print(f"First call execution time: {execution_time_first:.2f} seconds")
    print(f"Second call execution time: {execution_time_second:.2f} seconds")
    print(f"Speedup factor: {execution_time_first / execution_time_second:.2f}x")
    
    # Check that the second call is significantly faster
    assert execution_time_second < execution_time_first / 2  # At least 2x faster
    
    # Check that the results are identical
    assert result_first == result_second


@pytest.mark.performance
def test_memory_usage(large_dataset):
    """Test memory usage with large datasets."""
    analyzer = ResponseAnalyzer()
    
    # Measure memory usage during analysis
    memory_samples = []
    
    # Define a monitoring function
    def monitor_memory():
        memory_samples.append(get_memory_usage())
    
    # Patch the analyze_conversation_flows method to monitor memory
    original_method = analyzer.analyze_conversation_flows
    
    def patched_method(*args, **kwargs):
        monitor_memory()
        result = original_method(*args, **kwargs)
        monitor_memory()
        return result
    
    analyzer.analyze_conversation_flows = patched_method
    
    # Patch the analyze_response_times method to monitor memory
    original_method = analyzer.analyze_response_times
    
    def patched_method(*args, **kwargs):
        monitor_memory()
        result = original_method(*args, **kwargs)
        monitor_memory()
        return result
    
    analyzer.analyze_response_times = patched_method
    
    # Patch the detect_reciprocity_patterns method to monitor memory
    original_method = analyzer.detect_reciprocity_patterns
    
    def patched_method(*args, **kwargs):
        monitor_memory()
        result = original_method(*args, **kwargs)
        monitor_memory()
        return result
    
    analyzer.detect_reciprocity_patterns = patched_method
    
    # Measure initial memory
    initial_memory = get_memory_usage()
    memory_samples.append(initial_memory)
    
    # Run the analysis
    result = analyzer.analyze_response_patterns(large_dataset)
    
    # Measure final memory
    final_memory = get_memory_usage()
    memory_samples.append(final_memory)
    
    # Calculate memory statistics
    max_memory = max(memory_samples)
    memory_increase = max_memory - initial_memory
    
    # Log memory metrics
    print(f"\nMemory usage metrics:")
    print(f"Initial memory: {initial_memory:.2f} MB")
    print(f"Maximum memory: {max_memory:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")
    
    # Check memory requirements
    assert memory_increase < 1000  # Should use less than 1000 MB additional memory


@pytest.mark.performance
def test_processing_time(large_dataset):
    """Test that processing time scales linearly with dataset size."""
    analyzer = ResponseAnalyzer()
    
    # Create datasets of different sizes
    small_dataset = large_dataset.sample(frac=0.1, random_state=42)  # 10%
    medium_dataset = large_dataset.sample(frac=0.5, random_state=42)  # 50%
    
    # Measure processing time for each dataset
    start_time = time.time()
    analyzer.analyze_response_patterns(small_dataset)
    small_time = time.time() - start_time
    
    start_time = time.time()
    analyzer.analyze_response_patterns(medium_dataset)
    medium_time = time.time() - start_time
    
    start_time = time.time()
    analyzer.analyze_response_patterns(large_dataset)
    large_time = time.time() - start_time
    
    # Log timing metrics
    print(f"\nProcessing time scaling metrics:")
    print(f"Small dataset ({len(small_dataset)} records): {small_time:.2f} seconds")
    print(f"Medium dataset ({len(medium_dataset)} records): {medium_time:.2f} seconds")
    print(f"Large dataset ({len(large_dataset)} records): {large_time:.2f} seconds")
    
    # Calculate scaling factors
    small_to_medium_ratio = medium_time / small_time
    medium_to_large_ratio = large_time / medium_time
    
    # Expected ratios based on dataset size ratios
    expected_small_to_medium = len(medium_dataset) / len(small_dataset)
    expected_medium_to_large = len(large_dataset) / len(medium_dataset)
    
    print(f"Small to medium scaling factor: {small_to_medium_ratio:.2f} (expected: {expected_small_to_medium:.2f})")
    print(f"Medium to large scaling factor: {medium_to_large_ratio:.2f} (expected: {expected_medium_to_large:.2f})")
    
    # Check that scaling is approximately linear (with some tolerance)
    # The ratio of processing times should be similar to the ratio of dataset sizes
    assert small_to_medium_ratio < expected_small_to_medium * 1.5
    assert medium_to_large_ratio < expected_medium_to_large * 1.5
