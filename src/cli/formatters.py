"""
Output Formatters Module
-------------------
Handles formatting of output data in various formats.
"""

import json
from typing import List, Dict, Any

class TableFormatter:
    """Formatter for table output."""
    
    def format(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a table.
        
        Args:
            data: List of dictionaries containing data to format
            
        Returns:
            Formatted table as a string
        """
        if not data:
            return ""
        
        # Get column names from the first row
        columns = list(data[0].keys())
        
        # Calculate column widths
        column_widths = {col: len(col) for col in columns}
        for row in data:
            for col in columns:
                column_widths[col] = max(column_widths[col], len(str(row[col])))
        
        # Create table header
        header = " | ".join(f"{col:{column_widths[col]}}" for col in columns)
        separator = "-+-".join("-" * column_widths[col] for col in columns)
        
        # Create table rows
        rows = []
        for row in data:
            rows.append(" | ".join(f"{str(row[col]):{column_widths[col]}}" for col in columns))
        
        # Combine header, separator, and rows
        table = f"{header}\n{separator}\n" + "\n".join(rows)
        return table

class JSONFormatter:
    """Formatter for JSON output."""
    
    def format(self, data: List[Dict[str, Any]]) -> str:
        """Format data as JSON.
        
        Args:
            data: List of dictionaries containing data to format
            
        Returns:
            Formatted JSON as a string
        """
        return json.dumps(data, indent=4)

class TextFormatter:
    """Formatter for plain text output."""
    
    def format(self, data: List[Dict[str, Any]]) -> str:
        """Format data as plain text.
        
        Args:
            data: List of dictionaries containing data to format
            
        Returns:
            Formatted plain text as a string
        """
        lines = []
        for row in data:
            lines.append(", ".join(f"{key}: {value}" for key, value in row.items()))
        return "\n".join(lines)
