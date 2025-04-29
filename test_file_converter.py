import unittest
import pandas as pd
import os
import tempfile
from file_converter import convert_file

class TestFileConverter(unittest.TestCase):

    def setUp(self):
        # Create a sample DataFrame that mimics the input format
        self.sample_data = pd.DataFrame({
            'Line': ['2693037499', '2693037499'],
            'Date': ['01/20/2025', '01/20/2025'],
            'Time': ['09:27 AM', '10:48 AM'],
            'Direction': ['Received', 'Received'],
            'To/From': ['6180930000', '7297250000'],
            'Message Type': ['Text', 'Text']
        })

        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.test_dir, 'input.xlsx')
        self.output_file = os.path.join(self.test_dir, 'output.xlsx')

        # Save the sample data to an Excel file
        self.sample_data.to_excel(self.input_file, index=False)

    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        # Clean up any other files in the directory
        for file in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

        # Try to remove the directory
        try:
            os.rmdir(self.test_dir)
        except OSError as e:
            print(f"Warning: Could not remove temp directory {self.test_dir}: {e}")

    def test_column_renaming(self):
        """Test that columns are correctly renamed"""
        result = convert_file(self.input_file, self.output_file)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

        # Read the output file
        df = pd.read_excel(self.output_file)

        # Check that the required columns exist
        self.assertIn('phone_number', df.columns)
        self.assertIn('message_type', df.columns)
        self.assertIn('timestamp', df.columns)

    def test_timestamp_creation(self):
        """Test that Date and Time are correctly combined into timestamp"""
        result = convert_file(self.input_file, self.output_file)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        df = pd.read_excel(self.output_file)

        # Check that timestamp is a datetime column
        self.assertTrue(pd.api.types.is_datetime64_dtype(df['timestamp']))

        # Check the first timestamp value
        expected_timestamp = pd.to_datetime('01/20/2025 09:27 AM', format='%m/%d/%Y %I:%M %p')
        self.assertEqual(df['timestamp'][0], expected_timestamp)

    def test_phone_number_cleaning(self):
        """Test that phone numbers are properly cleaned"""
        # Create data with messy phone numbers
        messy_data = pd.DataFrame({
            'Line': ['2693037499'],
            'Date': ['01/20/2025'],
            'Time': ['09:27 AM'],
            'Direction': ['Received'],
            'To/From': ['(618) 093-0000'],  # Formatted phone number
            'Message Type': ['Text']
        })
        messy_file = os.path.join(self.test_dir, 'messy.xlsx')
        messy_data.to_excel(messy_file, index=False)

        convert_file(messy_file, self.output_file)
        df = pd.read_excel(self.output_file, dtype={'phone_number': str})

        # Check that phone number is cleaned
        self.assertEqual(df['phone_number'][0], '6180930000')

        # Clean up
        os.remove(messy_file)

    def test_validation_errors(self):
        """Test that validation errors are properly reported"""
        # Create data with missing values
        invalid_data = pd.DataFrame({
            'Line': ['2693037499'],
            'Date': ['01/20/2025'],
            'Time': ['09:27 AM'],
            'Direction': ['Received'],
            'To/From': [None],  # Missing phone number
            'Message Type': ['Text']
        })
        invalid_file = os.path.join(self.test_dir, 'invalid.xlsx')
        invalid_data.to_excel(invalid_file, index=False)

        result = convert_file(invalid_file, self.output_file)

        # Check that validation issues are reported
        self.assertIsInstance(result, list)
        self.assertTrue(any('phone_number' in issue for issue in result))

        # Clean up
        os.remove(invalid_file)

    def test_invalid_date_format(self):
        """Test handling of invalid date formats"""
        # Create data with invalid date format
        invalid_data = pd.DataFrame({
            'Line': ['2693037499'],
            'Date': ['2025-01-20'],  # Different format
            'Time': ['09:27 AM'],
            'Direction': ['Received'],
            'To/From': ['6180930000'],
            'Message Type': ['Text']
        })
        invalid_file = os.path.join(self.test_dir, 'invalid_date.xlsx')
        invalid_data.to_excel(invalid_file, index=False)

        result = convert_file(invalid_file, self.output_file)

        # Check that date format issues are reported
        self.assertIsInstance(result, list)
        self.assertTrue(any('Date/Time' in issue for issue in result))

        # Clean up
        os.remove(invalid_file)

if __name__ == '__main__':
    unittest.main()
