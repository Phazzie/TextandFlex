import pytest
from src.cli.formatters import TableFormatter, JSONFormatter, TextFormatter

def test_table_formatter():
    formatter = TableFormatter()
    data = [
        {"Name": "Alice", "Age": 30, "City": "New York"},
        {"Name": "Bob", "Age": 25, "City": "Los Angeles"},
        {"Name": "Charlie", "Age": 35, "City": "Chicago"}
    ]
    expected_output = (
        "+---------+-----+-------------+\n"
        "| Name    | Age | City        |\n"
        "+---------+-----+-------------+\n"
        "| Alice   | 30  | New York    |\n"
        "| Bob     | 25  | Los Angeles |\n"
        "| Charlie | 35  | Chicago     |\n"
        "+---------+-----+-------------+\n"
    )
    assert formatter.format(data) == expected_output

def test_json_formatter():
    formatter = JSONFormatter()
    data = [
        {"Name": "Alice", "Age": 30, "City": "New York"},
        {"Name": "Bob", "Age": 25, "City": "Los Angeles"},
        {"Name": "Charlie", "Age": 35, "City": "Chicago"}
    ]
    expected_output = (
        '[\n'
        '    {\n'
        '        "Name": "Alice",\n'
        '        "Age": 30,\n'
        '        "City": "New York"\n'
        '    },\n'
        '    {\n'
        '        "Name": "Bob",\n'
        '        "Age": 25,\n'
        '        "City": "Los Angeles"\n'
        '    },\n'
        '    {\n'
        '        "Name": "Charlie",\n'
        '        "Age": 35,\n'
        '        "City": "Chicago"\n'
        '    }\n'
        ']'
    )
    assert formatter.format(data) == expected_output

def test_text_formatter():
    formatter = TextFormatter()
    data = [
        {"Name": "Alice", "Age": 30, "City": "New York"},
        {"Name": "Bob", "Age": 25, "City": "Los Angeles"},
        {"Name": "Charlie", "Age": 35, "City": "Chicago"}
    ]
    expected_output = (
        "Name: Alice, Age: 30, City: New York\n"
        "Name: Bob, Age: 25, City: Los Angeles\n"
        "Name: Charlie, Age: 35, City: Chicago\n"
    )
    assert formatter.format(data) == expected_output

def test_table_formatter_column_alignment():
    formatter = TableFormatter()
    data = [
        {"Name": "Alice", "Age": 30, "City": "New York"},
        {"Name": "Bob", "Age": 25, "City": "Los Angeles"},
        {"Name": "Charlie", "Age": 35, "City": "Chicago"}
    ]
    expected_output = (
        "+---------+-----+-------------+\n"
        "| Name    | Age | City        |\n"
        "+---------+-----+-------------+\n"
        "| Alice   | 30  | New York    |\n"
        "| Bob     | 25  | Los Angeles |\n"
        "| Charlie | 35  | Chicago     |\n"
        "+---------+-----+-------------+\n"
    )
    assert formatter.format(data) == expected_output

def test_table_formatter_data_formatting():
    formatter = TableFormatter()
    data = [
        {"Name": "Alice", "Age": 30, "City": "New York"},
        {"Name": "Bob", "Age": 25, "City": "Los Angeles"},
        {"Name": "Charlie", "Age": 35, "City": "Chicago"}
    ]
    expected_output = (
        "+---------+-----+-------------+\n"
        "| Name    | Age | City        |\n"
        "+---------+-----+-------------+\n"
        "| Alice   | 30  | New York    |\n"
        "| Bob     | 25  | Los Angeles |\n"
        "| Charlie | 35  | Chicago     |\n"
        "+---------+-----+-------------+\n"
    )
    assert formatter.format(data) == expected_output

def test_color_and_styling():
    formatter = TableFormatter()
    data = [
        {"Name": "Alice", "Age": 30, "City": "New York"},
        {"Name": "Bob", "Age": 25, "City": "Los Angeles"},
        {"Name": "Charlie", "Age": 35, "City": "Chicago"}
    ]
    expected_output = (
        "\033[1m+---------+-----+-------------+\033[0m\n"
        "\033[1m| Name    | Age | City        |\033[0m\n"
        "\033[1m+---------+-----+-------------+\033[0m\n"
        "| Alice   | 30  | New York    |\n"
        "| Bob     | 25  | Los Angeles |\n"
        "| Charlie | 35  | Chicago     |\n"
        "\033[1m+---------+-----+-------------+\033[0m\n"
    )
    assert formatter.format(data) == expected_output
