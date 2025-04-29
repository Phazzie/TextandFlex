# Phone Records File Converter

A simple utility to convert phone records Excel files to the format expected by the TextandFlex application. Features a modern, user-friendly interface with support for processing multiple files simultaneously.

## Purpose

This tool helps you convert Excel files containing phone records to a format that is compatible with the TextandFlex application. It features a modern, colorful interface and can process multiple files at once. The converter handles:

- Column renaming to match expected format
- Phone number cleaning (removing formatting characters)
- Date and time conversion to proper timestamp format
- Validation of required fields

## Requirements

- Python 3.6 or higher
- Required packages:
  - pandas
  - openpyxl
  - tkinter (usually included with Python)

## Installation

1. Ensure you have Python installed
2. Install required packages:
   ```
   pip install pandas openpyxl
   ```

## Usage

### GUI Application

Run the GUI application:

```
python phone_records_converter_gui.py
```

1. Click "Add Files..." to select one or more input Excel files
2. Choose whether to save files to the project root directory (checked by default) or specify a custom output directory
3. Click "Convert Files" to process all files
4. Monitor the progress bar and check the status area for conversion results and any warnings

### Command Line Usage

You can use the converter directly from Python for a single file:

```python
from file_converter import convert_file

result = convert_file("input.xlsx", "output.xlsx")
if isinstance(result, list) and not result:
    print("Conversion successful!")
else:
    print("Conversion completed with warnings:")
    for issue in result:
        print(f"- {issue}")
```

Or process multiple files at once:

```python
from file_converter import batch_convert_files

# Convert multiple files and save them to a specific directory
input_files = ["file1.xlsx", "file2.xlsx", "file3.xlsx"]
output_dir = "converted_files"

results = batch_convert_files(input_files, output_dir)

# Check results for each file
for input_file, issues in results.items():
    if not issues:
        print(f"{input_file}: Conversion successful!")
    else:
        print(f"{input_file}: Converted with warnings:")
        for issue in issues:
            print(f"  - {issue}")
```

## Expected Input Format

The tool expects Excel files with the following columns:

- Line
- Date (in format MM/DD/YYYY)
- Time (in format HH:MM AM/PM)
- Direction
- To/From (phone numbers)
- Message Type

## Output Format

The converted file will have the following columns:

- line
- direction
- phone_number (cleaned)
- message_type
- timestamp (combined from Date and Time)
- Date and Time (original columns preserved)

## Troubleshooting

If you encounter issues:

1. Check that your Excel file has all the required columns
2. Ensure date and time formats match the expected formats
3. Check for missing values in required fields
4. Look at the status area in the GUI for specific warnings or errors

## Development

### Running Tests

```
python -m unittest test_file_converter.py
```

### Project Structure

- `phone_records_converter_gui.py` - GUI application with modern, colorful interface
- `file_converter.py` - Core conversion logic
- `test_file_converter.py` - Unit tests
- `icon.ico` - Application icon
- `create_icon.py` - Script to generate the application icon
