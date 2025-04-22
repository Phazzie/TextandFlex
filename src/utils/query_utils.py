"""
Query Utilities Module
-------------------
Utilities for building and optimizing complex queries.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
import pandas as pd

from ..logger import get_logger
from ..data_layer.exceptions import QueryError

logger = get_logger("query_utils")

# Valid operators for query conditions
VALID_OPERATORS = [
    "==", "!=", ">", ">=", "<", "<=", 
    "in", "not in", "contains", "startswith", "endswith"
]

def build_query(
    dataset: str,
    conditions: Optional[List[Tuple[str, str, Any]]] = None,
    combine: str = "and",
    select: Optional[List[str]] = None,
    group_by: Optional[Union[str, List[str]]] = None,
    aggregate: Optional[Dict[str, str]] = None,
    order_by: Optional[str] = None,
    ascending: bool = True,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Build a query dictionary for complex queries.
    
    Args:
        dataset: Name of the dataset to query
        conditions: List of conditions as (column, operator, value) tuples
        combine: How to combine conditions ('and' or 'or')
        select: List of columns to include in the result
        group_by: Column or list of columns to group by
        aggregate: Dictionary mapping columns to aggregation functions
        order_by: Column to order by
        ascending: Whether to sort in ascending order
        limit: Maximum number of rows to return
        
    Returns:
        Query dictionary
    """
    query = {
        "dataset": dataset,
        "conditions": conditions or [],
        "combine": combine,
        "select": select,
        "group_by": group_by,
        "aggregate": aggregate,
        "order_by": order_by,
        "ascending": ascending,
        "limit": limit
    }
    
    logger.info(f"Built query for dataset '{dataset}' with {len(conditions or [])} conditions")
    return query

def optimize_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize a query for better performance.
    
    Args:
        query: Query dictionary
        
    Returns:
        Optimized query dictionary
    """
    optimized = query.copy()
    
    # Optimization 1: Reorder conditions to filter out more rows early
    if optimized.get("conditions"):
        # This is a simple optimization that puts equality conditions first
        # In a real system, you would use statistics about the data to make better decisions
        equality_conditions = []
        other_conditions = []
        
        for condition in optimized["conditions"]:
            if len(condition) == 3:
                column, op, value = condition
                if op == "==":
                    equality_conditions.append(condition)
                else:
                    other_conditions.append(condition)
        
        optimized["conditions"] = equality_conditions + other_conditions
    
    # Optimization 2: Limit columns early if possible
    if optimized.get("select") and not optimized.get("group_by"):
        # Add any columns used in conditions or sorting
        required_columns = set(optimized.get("select", []))
        
        for condition in optimized.get("conditions", []):
            if len(condition) >= 1:
                required_columns.add(condition[0])
        
        if optimized.get("order_by"):
            required_columns.add(optimized["order_by"])
        
        optimized["_required_columns"] = list(required_columns)
    
    logger.info(f"Optimized query for dataset '{query.get('dataset')}'")
    return optimized

def validate_query(query: Dict[str, Any]) -> bool:
    """Validate a query dictionary.
    
    Args:
        query: Query dictionary
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    # Validate dataset
    if not query.get("dataset"):
        raise ValueError("Query must specify a dataset")
    
    # Validate conditions
    for condition in query.get("conditions", []):
        if not isinstance(condition, tuple) or len(condition) != 3:
            raise ValueError(f"Invalid condition format: {condition}")
        
        column, op, value = condition
        if not isinstance(column, str):
            raise ValueError(f"Column name must be a string: {column}")
        
        if op not in VALID_OPERATORS:
            raise ValueError(f"Invalid operator: {op}")
    
    # Validate combine method
    if query.get("combine") not in ["and", "or", None]:
        raise ValueError(f"Invalid combine method: {query.get('combine')}")
    
    # Validate limit
    if query.get("limit") is not None and (not isinstance(query["limit"], int) or query["limit"] < 0):
        raise ValueError(f"Limit must be a non-negative integer: {query.get('limit')}")
    
    logger.info(f"Validated query for dataset '{query.get('dataset')}'")
    return True

def execute_query(query: Dict[str, Any], dataframe: pd.DataFrame) -> pd.DataFrame:
    """Execute a query on a DataFrame.
    
    Args:
        query: Query dictionary
        dataframe: DataFrame to query
        
    Returns:
        Result DataFrame
    """
    from ..data_layer.complex_query import QueryBuilder
    
    try:
        # Validate the query
        validate_query(query)
        
        # Create query builder
        builder = QueryBuilder(dataframe)
        
        # Add conditions
        for column, op, value in query.get("conditions", []):
            if query.get("combine") == "or":
                builder.or_where(column, op, value)
            else:
                builder.and_where(column, op, value)
        
        # Add select
        if query.get("select"):
            builder.select(query["select"])
        
        # Add group by and aggregation
        if query.get("group_by"):
            builder.group_by(query["group_by"])
            
            if query.get("aggregate"):
                builder.aggregate(query["aggregate"])
        
        # Add order by
        if query.get("order_by"):
            builder.order_by(query["order_by"], query.get("ascending", True))
        
        # Add limit
        if query.get("limit") is not None:
            builder.limit(query["limit"])
        
        # Execute the query
        result = builder.execute()
        logger.info(f"Executed query, returned {len(result)} rows")
        return result
    
    except Exception as e:
        error_msg = f"Error executing query: {str(e)}"
        logger.error(error_msg)
        raise QueryError(error_msg)
