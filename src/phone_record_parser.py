"""
Phone Records Parser
-------------------
Module for parsing phone records from Excel files.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union


class PhoneRecordParser:
    """Parser for phone records from Excel spreadsheets."""
    
    def __init__(self, file_path: str = None):
        """Initialize the parser.
        
        Args:
            file_path: Path to the Excel file to parse
        """
        self.file_path = file_path
        self.data = None
        self.summary = {}
    
    def load_file(self, file_path: Optional[str] = None) -> bool:
        """Load an Excel file containing phone records.
        
        Args:
            file_path: Path to the Excel file (optional if provided at init)
            
        Returns:
            bool: True if file loaded successfully, False otherwise
        """
        if file_path:
            self.file_path = file_path
            
        if not self.file_path:
            raise ValueError("No file path provided")
            
        try:
            self.data = pd.read_excel(self.file_path)
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def get_column_names(self) -> List[str]:
        """Get the column names from the loaded Excel file.
        
        Returns:
            List of column names
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_file() first.")
        
        return list(self.data.columns)
    
    def analyze_records(self, 
                      date_col: str = None, 
                      number_col: str = None, 
                      duration_col: str = None,
                      type_col: str = None) -> Dict:
        """Analyze the phone records to generate summary statistics.
        
        Args:
            date_col: Name of the column containing dates
            number_col: Name of the column containing phone numbers
            duration_col: Name of the column containing call duration
            type_col: Name of the column containing call type (incoming/outgoing)
            
        Returns:
            Dictionary with summary information
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_file() first.")
            
        # Auto-detect columns if not specified
        if not all([date_col, number_col, duration_col]):
            # Simple heuristic to find common column names
            cols = self.get_column_names()
            date_col = date_col or next((c for c in cols if 'date' in c.lower() or 'time' in c.lower()), None)
            number_col = number_col or next((c for c in cols if 'number' in c.lower() or 'phone' in c.lower()), None)
            duration_col = duration_col or next((c for c in cols if 'duration' in c.lower() or 'length' in c.lower()), None)
            type_col = type_col or next((c for c in cols if 'type' in c.lower() or 'direction' in c.lower()), None)
        
        summary = {
            "total_records": len(self.data),
            "date_range": None,
            "top_contacts": None,
            "call_duration": None,
            "call_types": None
        }
        
        # Process date range if date column exists
        if date_col and date_col in self.data:
            min_date = self.data[date_col].min()
            max_date = self.data[date_col].max()
            summary["date_range"] = {
                "start": min_date,
                "end": max_date,
                "days": (max_date - min_date).days if isinstance(min_date, datetime) else None
            }
        
        # Process top contacts if number column exists
        if number_col and number_col in self.data:
            contact_counts = self.data[number_col].value_counts().head(10)
            summary["top_contacts"] = contact_counts.to_dict()
        
        # Process call duration if duration column exists
        if duration_col and duration_col in self.data:
            summary["call_duration"] = {
                "total": self.data[duration_col].sum(),
                "average": self.data[duration_col].mean(),
                "max": self.data[duration_col].max(),
                "min": self.data[duration_col].min()
            }
        
        # Process call types if type column exists
        if type_col and type_col in self.data:
            type_counts = self.data[type_col].value_counts()
            summary["call_types"] = type_counts.to_dict()
        
        self.summary = summary
        return summary
    
    def get_records_by_number(self, number: str) -> pd.DataFrame:
        """Get all records for a specific phone number.
        
        Args:
            number: The phone number to filter by
            
        Returns:
            DataFrame containing only records for the specified number
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_file() first.")
            
        number_cols = [col for col in self.data.columns if 'number' in col.lower() or 'phone' in col.lower()]
        if not number_cols:
            raise ValueError("Could not identify a phone number column")
            
        return self.data[self.data[number_cols[0]] == number]
    
    def export_summary(self, output_path: str) -> bool:
        """Export the summary data to a CSV file.
        
        Args:
            output_path: Path where the summary CSV should be saved
            
        Returns:
            bool: True if export successful, False otherwise
        """
        if not self.summary:
            raise ValueError("No summary available. Call analyze_records() first.")
        
        try:
            # Convert the nested dictionary to a flattened dataframe
            summary_items = []
            for category, values in self.summary.items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        summary_items.append({
                            'Category': category,
                            'Metric': key,
                            'Value': value
                        })
                else:
                    summary_items.append({
                        'Category': category,
                        'Metric': 'value',
                        'Value': values
                    })
                    
            summary_df = pd.DataFrame(summary_items)
            summary_df.to_csv(output_path, index=False)
            return True
        except Exception as e:
            print(f"Error exporting summary: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    parser = PhoneRecordParser()
    sample_file = Path(__file__).parent.parent / "data" / "sample.xlsx"
    
    if sample_file.exists():
        parser.load_file(str(sample_file))
        print(f"Loaded file with {len(parser.data)} records")
        print(f"Columns: {parser.get_column_names()}")
        summary = parser.analyze_records()
        print(f"Summary: {summary}")
    else:
        print(f"Sample file not found at {sample_file}")
        print("Please place your phone records Excel file in the data directory")
