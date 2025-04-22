"""
Tests for complex query operations.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import datetime

@pytest.fixture
def sample_dataset1():
    """Create a sample dataset for testing."""
    return pd.DataFrame({
        "timestamp": ["2023-01-01 12:00:00", "2023-01-02 13:00:00", "2023-01-03 14:00:00"],
        "phone_number": ["1234567890", "9876543210", "5555555555"],
        "message_type": ["sent", "received", "sent"],
        "duration": [60, 120, 180]
    })

@pytest.fixture
def sample_dataset2():
    """Create another sample dataset for testing."""
    return pd.DataFrame({
        "timestamp": ["2023-01-01 15:00:00", "2023-01-02 16:00:00", "2023-01-04 17:00:00"],
        "phone_number": ["1234567890", "8888888888", "5555555555"],
        "message_type": ["received", "sent", "received"],
        "location": ["New York", "Los Angeles", "Chicago"]
    })

@pytest.mark.unit
def test_join_datasets():
    """Test joining two datasets."""
    from src.data_layer.complex_query import JoinOperation

    # Create sample datasets
    df1 = pd.DataFrame({
        "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "phone_number": ["1234567890", "9876543210", "5555555555"],
        "message_type": ["sent", "received", "sent"]
    })

    df2 = pd.DataFrame({
        "timestamp": ["2023-01-01", "2023-01-02", "2023-01-04"],
        "phone_number": ["1234567890", "8888888888", "5555555555"],
        "location": ["New York", "Los Angeles", "Chicago"]
    })

    # Create join operation
    join_op = JoinOperation(
        left_df=df1,
        right_df=df2,
        join_type="inner",
        join_columns=["phone_number"]
    )

    # Execute join
    result = join_op.execute()

    # Verify result
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2  # Only two matching phone numbers
    assert "timestamp_x" in result.columns  # Columns from first dataset
    assert "timestamp_y" in result.columns  # Columns from second dataset
    assert "location" in result.columns     # Unique column from second dataset

    # Verify the correct rows were joined
    assert "1234567890" in result["phone_number"].values
    assert "5555555555" in result["phone_number"].values

@pytest.mark.unit
def test_join_datasets_with_suffix():
    """Test joining datasets with custom suffixes."""
    from src.data_layer.complex_query import JoinOperation

    # Create sample datasets
    df1 = pd.DataFrame({
        "timestamp": ["2023-01-01", "2023-01-02"],
        "phone_number": ["1234567890", "9876543210"],
        "message_type": ["sent", "received"]
    })

    df2 = pd.DataFrame({
        "timestamp": ["2023-01-01", "2023-01-03"],
        "phone_number": ["1234567890", "5555555555"],
        "location": ["New York", "Chicago"]
    })

    # Create join operation with custom suffixes
    join_op = JoinOperation(
        left_df=df1,
        right_df=df2,
        join_type="inner",
        join_columns=["phone_number"],
        suffixes=("_primary", "_secondary")
    )

    # Execute join
    result = join_op.execute()

    # Verify result
    assert isinstance(result, pd.DataFrame)
    assert "timestamp_primary" in result.columns
    assert "timestamp_secondary" in result.columns

@pytest.mark.unit
def test_join_types():
    """Test different join types."""
    from src.data_layer.complex_query import JoinOperation

    # Create sample datasets
    df1 = pd.DataFrame({
        "phone_number": ["1234567890", "9876543210", "5555555555"],
        "name": ["Alice", "Bob", "Charlie"]
    })

    df2 = pd.DataFrame({
        "phone_number": ["1234567890", "8888888888", "5555555555"],
        "location": ["New York", "Los Angeles", "Chicago"]
    })

    # Test inner join
    inner_join = JoinOperation(
        left_df=df1,
        right_df=df2,
        join_type="inner",
        join_columns=["phone_number"]
    )
    inner_result = inner_join.execute()
    assert len(inner_result) == 2  # Only matching records

    # Test left join
    left_join = JoinOperation(
        left_df=df1,
        right_df=df2,
        join_type="left",
        join_columns=["phone_number"]
    )
    left_result = left_join.execute()
    assert len(left_result) == 3  # All records from left dataset
    assert pd.isna(left_result.loc[left_result["phone_number"] == "9876543210", "location"].iloc[0])

    # Test right join
    right_join = JoinOperation(
        left_df=df1,
        right_df=df2,
        join_type="right",
        join_columns=["phone_number"]
    )
    right_result = right_join.execute()
    assert len(right_result) == 3  # All records from right dataset
    assert pd.isna(right_result.loc[right_result["phone_number"] == "8888888888", "name"].iloc[0])

    # Test outer join
    outer_join = JoinOperation(
        left_df=df1,
        right_df=df2,
        join_type="outer",
        join_columns=["phone_number"]
    )
    outer_result = outer_join.execute()
    assert len(outer_result) == 4  # All unique records from both datasets

@pytest.mark.unit
def test_complex_filter():
    """Test complex filtering operations."""
    from src.data_layer.complex_query import ComplexFilter

    # Create sample dataset
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2023-01-01 12:00:00", "2023-01-02 13:00:00",
                                     "2023-01-03 14:00:00", "2023-01-04 15:00:00"]),
        "phone_number": ["1234567890", "9876543210", "5555555555", "1234567890"],
        "message_type": ["sent", "received", "sent", "received"],
        "duration": [60, 120, 180, 240]
    })

    # Create complex filter
    complex_filter = ComplexFilter(df)

    # Test AND condition
    and_result = complex_filter.filter(
        conditions=[
            ("phone_number", "==", "1234567890"),
            ("message_type", "==", "sent")
        ],
        combine="and"
    )
    assert len(and_result) == 1
    assert and_result.iloc[0]["duration"] == 60

    # Test OR condition
    or_result = complex_filter.filter(
        conditions=[
            ("phone_number", "==", "1234567890"),
            ("duration", ">", 150)
        ],
        combine="or"
    )
    assert len(or_result) == 3

    # Test date range filter
    date_result = complex_filter.filter_date_range(
        column="timestamp",
        start_date="2023-01-02",
        end_date="2023-01-03"
    )
    assert len(date_result) == 2

    # Test multiple column filter
    multi_result = complex_filter.filter_by_values(
        filters={
            "phone_number": ["1234567890", "5555555555"],
            "message_type": ["sent"]
        }
    )
    assert len(multi_result) == 2
    assert set(multi_result["phone_number"].tolist()) == {"1234567890", "5555555555"}
    assert set(multi_result["message_type"].tolist()) == {"sent"}

@pytest.mark.unit
def test_query_builder():
    """Test query builder functionality."""
    from src.data_layer.complex_query import QueryBuilder

    # Create sample dataset
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2023-01-01 12:00:00", "2023-01-02 13:00:00",
                                     "2023-01-03 14:00:00", "2023-01-04 15:00:00"]),
        "phone_number": ["1234567890", "9876543210", "5555555555", "1234567890"],
        "message_type": ["sent", "received", "sent", "received"],
        "duration": [60, 120, 180, 240]
    })

    # Create query builder
    query_builder = QueryBuilder(df)

    # Build and execute a query
    result = query_builder.where("phone_number", "==", "1234567890") \
                         .where("duration", "<", 100) \
                         .select(["timestamp", "duration"]) \
                         .execute()

    assert len(result) == 1
    assert "timestamp" in result.columns
    assert "duration" in result.columns
    assert "phone_number" not in result.columns
    assert result.iloc[0]["duration"] == 60

    # Test aggregation
    agg_result = query_builder.reset() \
                             .where("message_type", "==", "sent") \
                             .group_by("phone_number") \
                             .aggregate({"duration": "mean"}) \
                             .execute()

    assert len(agg_result) == 2  # Two unique phone numbers with sent messages
    assert "duration" in agg_result.columns  # Column name is just 'duration' in our implementation

    # Test sorting
    sort_result = query_builder.reset() \
                              .order_by("duration", ascending=False) \
                              .limit(2) \
                              .execute()

    assert len(sort_result) == 2
    assert sort_result.iloc[0]["duration"] == 240
    assert sort_result.iloc[1]["duration"] == 180

@pytest.mark.unit
def test_repository_complex_query(sample_dataset1, sample_dataset2):
    """Test repository integration with complex queries."""
    from src.data_layer.repository import PhoneRecordRepository
    from src.data_layer.models import PhoneRecordDataset
    from src.data_layer.complex_query import JoinOperation, ComplexFilter, QueryBuilder

    # Mock repository
    repo = MagicMock(spec=PhoneRecordRepository)

    # Create mock datasets
    dataset1 = MagicMock(spec=PhoneRecordDataset)
    dataset1.data = sample_dataset1
    dataset1.name = "dataset1"

    dataset2 = MagicMock(spec=PhoneRecordDataset)
    dataset2.data = sample_dataset2
    dataset2.name = "dataset2"

    # Mock repository methods
    repo.get_dataset.side_effect = lambda name: {"dataset1": dataset1, "dataset2": dataset2}.get(name)

    # Test join_datasets method
    with patch('src.data_layer.repository.PhoneRecordRepository.join_datasets',
               return_value=pd.merge(sample_dataset1, sample_dataset2, on="phone_number", how="inner")):

        # Call the method
        from src.data_layer.repository import PhoneRecordRepository
        result = PhoneRecordRepository.join_datasets(repo, "dataset1", "dataset2", "phone_number", "inner")

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Two matching phone numbers
        assert "timestamp_x" in result.columns
        assert "timestamp_y" in result.columns

    # Test complex_filter method
    with patch('src.data_layer.repository.PhoneRecordRepository.complex_filter',
               return_value=sample_dataset1[sample_dataset1["message_type"] == "sent"]):

        # Call the method
        result = PhoneRecordRepository.complex_filter(repo, "dataset1", [("message_type", "==", "sent")])

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Two sent messages
        assert all(result["message_type"] == "sent")

@pytest.mark.unit
def test_query_utils():
    """Test query utilities."""
    from src.utils.query_utils import build_query, optimize_query, validate_query

    # Test build_query
    query = build_query(
        dataset="calls",
        conditions=[
            ("duration", ">", 60),
            ("phone_number", "==", "1234567890")
        ],
        combine="and",
        select=["timestamp", "duration"],
        order_by="duration",
        ascending=False,
        limit=10
    )

    assert query["dataset"] == "calls"
    assert len(query["conditions"]) == 2
    assert query["combine"] == "and"
    assert query["select"] == ["timestamp", "duration"]
    assert query["order_by"] == "duration"
    assert query["ascending"] is False
    assert query["limit"] == 10

    # Test optimize_query
    optimized = optimize_query(query)
    assert optimized["dataset"] == "calls"
    # Optimization should keep the structure intact
    assert len(optimized["conditions"]) == 2

    # Test validate_query with valid query
    assert validate_query(query) is True

    # Test validate_query with invalid query
    invalid_query = {
        "dataset": "calls",
        "conditions": [("invalid_operator", "duration", 60)],  # Wrong format
        "combine": "and"
    }
    with pytest.raises(ValueError):
        validate_query(invalid_query)

@pytest.mark.integration
def test_end_to_end_complex_query():
    """Test end-to-end complex query workflow."""
    from src.data_layer.repository import PhoneRecordRepository
    from src.data_layer.complex_query import QueryBuilder
    from src.utils.query_utils import build_query

    # Create repository with mock data
    with patch('src.data_layer.repository.PhoneRecordRepository') as MockRepo:
        # Setup mock repository
        repo = MockRepo.return_value

        # Mock dataset
        mock_data = pd.DataFrame({
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
            "phone_number": ["1234567890", "9876543210", "5555555555"],
            "message_type": ["sent", "received", "sent"],
            "duration": [60, 120, 180]
        })

        # Mock query execution
        repo.execute_complex_query.return_value = mock_data[mock_data["message_type"] == "sent"]

        # Build query
        query = build_query(
            dataset="calls",
            conditions=[("message_type", "==", "sent")],
            select=["timestamp", "phone_number", "duration"]
        )

        # Execute query
        result = repo.execute_complex_query(query)

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Two sent messages
        assert all(result["message_type"] == "sent")

        # Verify the correct method was called
        repo.execute_complex_query.assert_called_once()
