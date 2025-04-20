"""
Phone Analyzer Application
-----------------------
Main application entry point.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .data_layer.excel_parser import ExcelParser
from .data_layer.repository import PhoneRecordRepository
from .analysis_layer.basic_statistics import BasicStatisticsAnalyzer
from .logger import app_logger as logger

def main():
    """Main application entry point."""
    logger.info("Starting Phone Analyzer application")
    
    # Initialize components
    parser = ExcelParser()
    repository = PhoneRecordRepository()
    analyzer = BasicStatisticsAnalyzer()
    
    # Check for sample data
    sample_file = Path(__file__).parent.parent / "data" / "sample.xlsx"
    
    if sample_file.exists():
        logger.info(f"Found sample file: {sample_file}")
        
        # Parse file
        df, mapping, error = parser.parse_and_detect(sample_file)
        
        if df is not None:
            logger.info(f"Parsed sample file with {len(df)} records")
            logger.info(f"Detected column mapping: {mapping}")
            
            # Add to repository
            if repository.add_dataset("sample", df, mapping):
                logger.info("Added sample dataset to repository")
                
                # Analyze data
                stats, error = analyzer.analyze(df, mapping)
                
                if stats:
                    logger.info("Analysis complete")
                    logger.info(f"Total records: {stats.total_records}")
                    
                    if stats.date_range:
                        logger.info(f"Date range: {stats.date_range.start} to {stats.date_range.end} ({stats.date_range.days} days)")
                    
                    if stats.top_contacts:
                        logger.info(f"Top contact: {stats.top_contacts[0].number} ({stats.top_contacts[0].count} records, {stats.top_contacts[0].percentage:.2f}%)")
                else:
                    logger.error(f"Analysis failed: {error}")
            else:
                logger.error(f"Failed to add dataset: {repository.last_error}")
        else:
            logger.error(f"Failed to parse sample file: {error}")
    else:
        logger.warning(f"Sample file not found at {sample_file}")
        logger.info("Please place your phone records Excel file in the data directory")

if __name__ == "__main__":
    main()
