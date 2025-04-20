"""
Script to generate sample Excel files for testing.
"""
import pandas as pd
import numpy as np
import os
from pathlib import Path

# Get the directory of this script
script_dir = Path(__file__).parent

# Create sample data
def create_sample_data():
    """Create a sample DataFrame with valid phone records data."""
    return pd.DataFrame({
        'timestamp': [
            '2023-01-01 12:00:00',
            '2023-01-01 12:30:00',
            '2023-01-01 13:00:00',
            '2023-01-01 14:00:00',
            '2023-01-01 15:00:00'
        ],
        'phone_number': [
            '+1 (123) 456-7890',
            '987-654-3210',
            '(555) 123-4567',
            '+44 7911 123456',
            '1234567890'
        ],
        'message_type': [
            'sent',
            'received',
            'sent',
            'received',
            'sent'
        ],
        'message_content': [
            'Hello, world!',
            'Hi there!',
            'How are you?',
            'I am fine, thanks!',
            'Great to hear that!'
        ]
    })

def create_malformed_data():
    """Create a sample DataFrame with malformed phone records data."""
    return pd.DataFrame({
        'date': [
            '2023-01-01 12:00:00',
            'invalid date',
            '2023-01-01 13:00:00',
            '2023/01/01 14:00',
            '15:00 01/01/2023'
        ],
        'contact': [
            '+1 (123) 456-7890',
            'abc',
            '(555) 123-4567',
            '',
            None
        ],
        'type': [
            'sent',
            'unknown',
            'SENT',
            'Received',
            'draft'
        ],
        'content': [
            'Hello, world!',
            'Hi there!',
            None,
            '',
            '  Whitespace  '
        ]
    })

def create_different_columns_data():
    """Create a sample DataFrame with differently named columns."""
    return pd.DataFrame({
        'Date': [
            '2023-01-01 12:00:00',
            '2023-01-01 12:30:00',
            '2023-01-01 13:00:00'
        ],
        'Phone': [
            '+1 (123) 456-7890',
            '987-654-3210',
            '(555) 123-4567'
        ],
        'Direction': [
            'Outgoing',
            'Incoming',
            'Outgoing'
        ],
        'Text': [
            'Hello, world!',
            'Hi there!',
            'How are you?'
        ]
    })

# Generate Excel files
def generate_excel_files():
    """Generate Excel files for testing."""
    # Create sample data
    sample_data = create_sample_data()
    malformed_data = create_malformed_data()
    different_columns_data = create_different_columns_data()
    
    # Save to Excel files
    sample_data.to_excel(script_dir / 'sample_data.xlsx', index=False)
    malformed_data.to_excel(script_dir / 'malformed_data.xlsx', index=False)
    different_columns_data.to_excel(script_dir / 'different_columns_data.xlsx', index=False)
    
    print(f"Generated Excel files in {script_dir}")

if __name__ == "__main__":
    generate_excel_files()
