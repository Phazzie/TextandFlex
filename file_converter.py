import pandas as pd
import re
import os
import logging
from typing import List, Dict, Union, Tuple, Optional
from converter_exceptions import (
    ConverterError, FileReadError, FileWriteError, MissingColumnsError,
    DataValidationError, DateTimeFormatError, EmptyDataError
)

# Set up logging
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = ['Line', 'Date', 'Time', 'Direction', 'To/From', 'Message Type']
COLUMN_MAPPING = {
    'To/From': 'phone_number',
    'Message Type': 'message_type',
    'Line': 'line',
    'Direction': 'direction'
}
REQUIRED_OUTPUT_COLUMNS = ['phone_number', 'message_type', 'timestamp']
DATE_FORMAT = '%m/%d/%Y'
TIME_FORMAT = '%I:%M %p'
DATETIME_FORMAT = f'{DATE_FORMAT} {TIME_FORMAT}'

def convert_file(input_path: str, output_path: str) -> List[str]:
    """
    Convert an Excel file from the original format to the format expected by the application.

    Args:
        input_path (str): Path to the input Excel file
        output_path (str): Path where the converted file will be saved

    Returns:
        List of validation issues (empty list if successful)

    Raises:
        FileReadError: If the input file cannot be read
        FileWriteError: If the output file cannot be written
        MissingColumnsError: If required columns are missing
        DataValidationError: If there are data validation issues
        DateTimeFormatError: If there's an error with date/time format
        EmptyDataError: If the input file contains no data
    """
    logger.info(f"Converting file: {input_path} -> {output_path}")

    # Track validation issues
    validation_issues = []

    try:
        # Check if file exists
        if not os.path.exists(input_path):
            error_msg = f"Input file does not exist: {input_path}"
            logger.error(error_msg)
            return [error_msg]

        # Read the Excel file
        try:
            df = pd.read_excel(input_path)
        except Exception as e:
            logger.error(f"Error reading file {input_path}: {str(e)}")
            raise FileReadError(input_path, e)

        # Check if dataframe is empty
        if df.empty:
            error_msg = f"File contains no data: {input_path}"
            logger.error(error_msg)
            return [error_msg]

        # Process the dataframe
        validation_issues = process_dataframe(df, output_path)

        # Log completion
        if not validation_issues:
            logger.info(f"Successfully converted file: {input_path}")
        else:
            logger.warning(f"Converted file with warnings: {input_path} - {len(validation_issues)} issues")
            for issue in validation_issues:
                logger.warning(f"  - {issue}")

        return validation_issues

    except ConverterError as e:
        # These are our custom exceptions, so we just pass them through
        logger.error(f"Converter error: {str(e)}")
        return [str(e)]
    except Exception as e:
        # Catch any other exceptions
        error_msg = f"Unexpected error processing file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [error_msg]


def process_dataframe(df: pd.DataFrame, output_path: str) -> List[str]:
    """
    Process a dataframe and save it to the output path.

    Args:
        df (pd.DataFrame): DataFrame to process
        output_path (str): Path where the converted file will be saved

    Returns:
        List of validation issues (empty list if successful)

    Raises:
        MissingColumnsError: If required columns are missing
        DataValidationError: If there are data validation issues
        DateTimeFormatError: If there's an error with date/time format
        FileWriteError: If the output file cannot be written
    """
    # Track validation issues
    validation_issues = []
    
    # Make column matching more flexible by normalizing column names (case-insensitive, ignore spaces)
    def normalize_column_name(name):
        return str(name).lower().replace(' ', '').replace('/', '').replace('-', '').replace('_', '')
    
    # Create mapping from normalized required columns to actual required columns
    normalized_required = {normalize_column_name(col): col for col in REQUIRED_COLUMNS}
    
    # Create mapping from actual dataframe columns to normalized dataframe columns
    normalized_df_columns = {normalize_column_name(col): col for col in df.columns}
    
    # Find missing columns using normalized names
    missing_columns = []
    column_mapping_actual = {}  # Will store mapping from required column name to actual df column name
    
    for norm_req_col, req_col in normalized_required.items():
        if norm_req_col in normalized_df_columns:
            # Found a match - store mapping from required name to actual df column name
            column_mapping_actual[req_col] = normalized_df_columns[norm_req_col]
        else:
            missing_columns.append(req_col)
            
    if missing_columns:
        error_msg = f"Input file is missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        return [error_msg]
    
    # Rename columns to standard format
    rename_map = {column_mapping_actual[req_col]: req_col for req_col in column_mapping_actual}
    df = df.rename(columns=rename_map)
    
    # Log the column mapping
    logger.debug(f"Mapped columns: {rename_map}")

    # Rename columns to match expected format
    df = df.rename(columns=COLUMN_MAPPING)

    # Log column mapping
    logger.debug(f"Renamed columns: {COLUMN_MAPPING}")

    # Clean phone numbers (remove non-numeric characters)
    try:
        # Handle potential errors in phone number processing
        df['phone_number'] = df['phone_number'].astype(str)
        df['phone_number'] = df['phone_number'].apply(
            lambda x: re.sub(r'\D', '', x) if pd.notna(x) and x != 'nan' else x
        )
        # Ensure phone_number stays as string type and not converted to numeric
        df['phone_number'] = df['phone_number'].astype(str)
        # Force pandas to keep it as string when saving to Excel
        df = df.astype({'phone_number': 'object'})

        logger.debug(f"Cleaned phone numbers in {len(df)} rows")
    except Exception as e:
        error_msg = f"Error cleaning phone numbers: {str(e)}"
        logger.error(error_msg)
        return [error_msg]

    # Check for missing phone numbers
    missing_phone_count = df['phone_number'].isna().sum() + (df['phone_number'] == 'nan').sum()
    if missing_phone_count > 0:
        error_msg = f"Missing phone numbers in {missing_phone_count} rows"
        logger.warning(error_msg)
        validation_issues.append(error_msg)

        # Provide more detailed information about which rows have missing phone numbers
        missing_indices = df.index[df['phone_number'].isna() | (df['phone_number'] == 'nan')].tolist()
        if missing_indices:
            row_numbers = [str(i + 2) for i in missing_indices[:5]]  # +2 for Excel row numbers (header + 1-based)
            if len(missing_indices) > 5:
                row_numbers.append(f"... and {len(missing_indices) - 5} more")
            validation_issues.append(f"Missing phone numbers in Excel rows: {', '.join(row_numbers)}")

        # Always return validation issues for missing phone numbers
        return validation_issues

    # Combine Date and Time into timestamp
    try:
        # First check if Date and Time columns have valid values
        date_errors = df['Date'].isna().sum()
        time_errors = df['Time'].isna().sum()

        if date_errors > 0 or time_errors > 0:
            if date_errors > 0:
                validation_issues.append(f"Missing Date values in {date_errors} rows")
            if time_errors > 0:
                validation_issues.append(f"Missing Time values in {time_errors} rows")

        # Try to combine Date and Time into timestamp
        df['timestamp'] = pd.to_datetime(
            df['Date'] + ' ' + df['Time'],
            format=DATETIME_FORMAT,
            errors='coerce'  # Convert errors to NaT for better handling
        )

        # Check for NaT values that indicate parsing errors
        nat_count = df['timestamp'].isna().sum()
        if nat_count > 0:
            # Find rows with parsing errors
            error_indices = df.index[df['timestamp'].isna()].tolist()
            # Get sample of problematic values for better error reporting
            sample_errors = []
            for idx in error_indices[:3]:  # Limit to 3 examples
                date_val = df.loc[idx, 'Date'] if 'Date' in df.columns else 'N/A'
                time_val = df.loc[idx, 'Time'] if 'Time' in df.columns else 'N/A'
                sample_errors.append(f"Row {idx+2}: Date='{date_val}', Time='{time_val}'")

            error_msg = f"Date/Time conversion failed for {nat_count} rows. Expected format: {DATETIME_FORMAT}"
            if sample_errors:
                error_msg += f" Examples: {'; '.join(sample_errors)}"

            validation_issues.append(error_msg)
            logger.warning(error_msg)
        else:
            logger.debug("Successfully converted all dates and times to timestamps")

    except Exception as e:
        error_msg = f"Date/Time conversion error: {str(e)}"
        logger.error(error_msg)
        validation_issues.append(error_msg)
        # Create empty timestamp column to allow saving the file
        df['timestamp'] = None

    # Validate required fields
    for field in REQUIRED_OUTPUT_COLUMNS:
        missing_count = df[field].isna().sum() + (df[field].astype(str) == 'nan').sum()
        if missing_count > 0:
            error_msg = f"Column {field} has {missing_count} missing values"
            logger.warning(error_msg)
            validation_issues.append(error_msg)

            # Provide more detailed information about which rows have missing values
            missing_indices = df.index[df[field].isna() | (df[field].astype(str) == 'nan')].tolist()
            if missing_indices:
                row_numbers = [str(i + 2) for i in missing_indices[:5]]  # +2 for Excel row numbers (header + 1-based)
                if len(missing_indices) > 5:
                    row_numbers.append(f"... and {len(missing_indices) - 5} more")
                validation_issues.append(f"Missing {field} values in Excel rows: {', '.join(row_numbers)}")

            # Return validation issues if any required field is missing
            return validation_issues

    # Save the converted file
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Add a special column to indicate this file has been processed by the converter
        # This can help the main application identify converted files
        df['_converted_by'] = 'TextandFlex Converter'
        df['_conversion_date'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

        # Ensure all required columns are present and in the right format
        # This is crucial for compatibility with the main application
        for field in REQUIRED_OUTPUT_COLUMNS:
            if field not in df.columns:
                logger.warning(f"Adding missing required column: {field}")
                df[field] = None

        # Ensure timestamp is in datetime format
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            except Exception as e:
                logger.warning(f"Could not convert timestamp to datetime: {str(e)}")

        # Save the file
        df.to_excel(output_path, index=False)
        logger.info(f"Successfully saved converted file to {output_path}")

        # Validate the saved file to ensure it can be loaded by the main application
        validation_result = validate_converted_file(output_path)
        if validation_result:
            logger.warning(f"Converted file may not be compatible with the main application: {', '.join(validation_result)}")
            validation_issues.extend(validation_result)
    except Exception as e:
        error_msg = f"Error saving file to {output_path}: {str(e)}"
        logger.error(error_msg)
        validation_issues.append(error_msg)
        raise FileWriteError(output_path, e)

    # Always return validation issues list, even if empty
    return validation_issues


def batch_convert_files(input_files: List[str], output_dir: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Convert multiple Excel files from the original format to the format expected by the application.

    Args:
        input_files (List[str]): List of paths to input Excel files
        output_dir (str, optional): Directory where converted files will be saved.
                                   If None, files will be saved in the same directory as input files with '_converted' suffix.

    Returns:
        Dict[str, List[str]]: Dictionary mapping input file paths to lists of validation issues

    Raises:
        FileReadError: If an input file cannot be read
        FileWriteError: If an output file cannot be written
    """
    logger.info(f"Batch converting {len(input_files)} files")

    # Validate input
    if not input_files:
        logger.warning("No input files provided for batch conversion")
        return {}
    results = {}

    # Create output directory if specified and doesn't exist
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        except Exception as e:
            error_msg = f"Could not create output directory {output_dir}: {str(e)}"
            logger.error(error_msg)
            # Return error for all files
            return {file: [error_msg] for file in input_files}

    for input_file in input_files:
        try:
            # Generate output path
            if output_dir:
                # Use the output directory with the original filename plus '_converted' suffix
                base_name = os.path.basename(input_file)
                name, ext = os.path.splitext(base_name)
                output_file = os.path.join(output_dir, f"{name}_converted{ext}")
            else:
                # Use the same directory as the input file
                dir_name, base_name = os.path.split(input_file)
                name, ext = os.path.splitext(base_name)
                output_file = os.path.join(dir_name, f"{name}_converted{ext}")

            # Convert the file
            validation_issues = convert_file(input_file, output_file)

            # Store the results
            results[input_file] = validation_issues

        except Exception as e:
            # Catch any unexpected errors and continue with the next file
            error_msg = f"Unexpected error processing {input_file}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results[input_file] = [error_msg]

    logger.info(f"Batch conversion completed. Processed {len(results)} files.")
    return results


def validate_converted_file(file_path: str) -> List[str]:
    """
    Validate that a converted file can be loaded by the main application.

    Args:
        file_path (str): Path to the converted file

    Returns:
        List of validation issues (empty list if successful)
    """
    validation_issues = []

    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return [f"File does not exist: {file_path}"]

        # Read the Excel file
        df = pd.read_excel(file_path)

        # Check if dataframe is empty
        if df.empty:
            return [f"File contains no data: {file_path}"]

        # Check for required columns
        missing_columns = [col for col in REQUIRED_OUTPUT_COLUMNS if col not in df.columns]
        if missing_columns:
            return [f"File is missing required columns: {', '.join(missing_columns)}"]

        # Check for missing values in required columns
        for field in REQUIRED_OUTPUT_COLUMNS:
            missing_count = df[field].isna().sum() + (df[field].astype(str) == 'nan').sum()
            if missing_count > 0:
                validation_issues.append(f"Column {field} has {missing_count} missing values")

        # Check timestamp format
        if 'timestamp' in df.columns:
            try:
                # Ensure timestamp is in datetime format
                if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

                # Check for NaT values
                nat_count = df['timestamp'].isna().sum()
                if nat_count > 0:
                    validation_issues.append(f"Invalid timestamp format in {nat_count} rows")
            except Exception as e:
                validation_issues.append(f"Error validating timestamp format: {str(e)}")

        return validation_issues

    except Exception as e:
        return [f"Error validating file: {str(e)}"]
