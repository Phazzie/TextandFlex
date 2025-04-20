"""
Result Formatter Module
-------------------
Format converters for different outputs of analysis results.
"""

import json
import csv
import io
from typing import Dict, List, Optional, Union, Callable, Any
from datetime import datetime

from .analysis_models import BasicStatistics
from ..logger import get_logger

logger = get_logger("result_formatter")

def format_as_text(stats: BasicStatistics) -> str:
    """Format statistics as plain text.
    
    Args:
        stats: BasicStatistics object
        
    Returns:
        Formatted text
    """
    if not stats:
        return "No statistics available"
    
    lines = []
    lines.append("Basic Statistics Summary")
    lines.append("=======================")
    lines.append(f"Total Records: {stats.total_records}")
    lines.append("")
    
    # Date range
    if stats.date_range:
        lines.append("Date Range")
        lines.append("---------")
        lines.append(f"Start Date: {stats.date_range.start}")
        lines.append(f"End Date: {stats.date_range.end}")
        lines.append(f"Duration: {stats.date_range.days} days")
        lines.append(f"Records: {stats.date_range.total_records}")
        lines.append("")
    
    # Top contacts
    if stats.top_contacts:
        lines.append("Top Contacts")
        lines.append("------------")
        for contact in stats.top_contacts:
            lines.append(f"Number: {contact.number}")
            lines.append(f"  Count: {contact.count} ({contact.percentage:.1f}%)")
            if contact.first_contact:
                lines.append(f"  First Contact: {contact.first_contact}")
            if contact.last_contact:
                lines.append(f"  Last Contact: {contact.last_contact}")
            lines.append("")
    
    # Duration statistics
    if stats.duration_stats:
        lines.append("Duration Statistics")
        lines.append("------------------")
        lines.append(f"Total Duration: {stats.duration_stats.total}")
        lines.append(f"Average Duration: {stats.duration_stats.average:.1f}")
        lines.append(f"Median Duration: {stats.duration_stats.median}")
        lines.append(f"Maximum Duration: {stats.duration_stats.max}")
        lines.append(f"Minimum Duration: {stats.duration_stats.min}")
        lines.append("")
    
    # Message type statistics
    if stats.type_stats:
        lines.append("Message Type Statistics")
        lines.append("----------------------")
        for type_name, count in stats.type_stats.types.items():
            lines.append(f"{type_name}: {count}")
        lines.append("")
    
    return "\n".join(lines)

def format_as_json(stats: BasicStatistics) -> str:
    """Format statistics as JSON.
    
    Args:
        stats: BasicStatistics object
        
    Returns:
        JSON string
    """
    if not stats:
        return json.dumps({"error": "No statistics available"})
    
    try:
        # Convert to dictionary
        stats_dict = stats.to_dict()
        
        # Convert datetime objects to ISO format strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        stats_dict = convert_datetime(stats_dict)
        
        # Convert to JSON
        return json.dumps(stats_dict, indent=2)
    
    except Exception as e:
        logger.error(f"Error formatting as JSON: {str(e)}")
        return json.dumps({"error": f"Error formatting as JSON: {str(e)}"})

def format_as_csv(stats: BasicStatistics) -> str:
    """Format statistics as CSV.
    
    Args:
        stats: BasicStatistics object
        
    Returns:
        CSV string
    """
    if not stats:
        return "error,No statistics available"
    
    try:
        # Create CSV output
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write basic info
        writer.writerow(["total_records", stats.total_records])
        
        # Write date range
        if stats.date_range:
            writer.writerow(["date_range_start", stats.date_range.start])
            writer.writerow(["date_range_end", stats.date_range.end])
            writer.writerow(["date_range_days", stats.date_range.days])
        
        # Write top contacts
        if stats.top_contacts:
            writer.writerow(["contact_number", "contact_count", "contact_percentage", "first_contact", "last_contact"])
            for contact in stats.top_contacts:
                writer.writerow([
                    contact.number,
                    contact.count,
                    contact.percentage,
                    contact.first_contact,
                    contact.last_contact
                ])
        
        # Write duration statistics
        if stats.duration_stats:
            writer.writerow(["duration_total", stats.duration_stats.total])
            writer.writerow(["duration_average", stats.duration_stats.average])
            writer.writerow(["duration_median", stats.duration_stats.median])
            writer.writerow(["duration_max", stats.duration_stats.max])
            writer.writerow(["duration_min", stats.duration_stats.min])
        
        # Write message type statistics
        if stats.type_stats:
            for type_name, count in stats.type_stats.types.items():
                writer.writerow([f"type_{type_name}", count])
        
        return output.getvalue()
    
    except Exception as e:
        logger.error(f"Error formatting as CSV: {str(e)}")
        return f"error,Error formatting as CSV: {str(e)}"

def format_as_html(stats: BasicStatistics) -> str:
    """Format statistics as HTML.
    
    Args:
        stats: BasicStatistics object
        
    Returns:
        HTML string
    """
    if not stats:
        return "<html><body><p>No statistics available</p></body></html>"
    
    try:
        html = []
        html.append("<html>")
        html.append("<head>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("h1 { color: #333366; }")
        html.append("h2 { color: #666699; }")
        html.append("table { border-collapse: collapse; width: 100%; }")
        html.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("th { background-color: #f2f2f2; }")
        html.append("tr:nth-child(even) { background-color: #f9f9f9; }")
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        
        # Basic info
        html.append(f"<h1>Basic Statistics Summary</h1>")
        html.append(f"<p><strong>Total Records:</strong> {stats.total_records}</p>")
        
        # Date range
        if stats.date_range:
            html.append("<h2>Date Range</h2>")
            html.append("<table>")
            html.append("<tr><th>Start Date</th><th>End Date</th><th>Duration (days)</th><th>Records</th></tr>")
            html.append(f"<tr><td>{stats.date_range.start}</td><td>{stats.date_range.end}</td>")
            html.append(f"<td>{stats.date_range.days}</td><td>{stats.date_range.total_records}</td></tr>")
            html.append("</table>")
        
        # Top contacts
        if stats.top_contacts:
            html.append("<h2>Top Contacts</h2>")
            html.append("<table>")
            html.append("<tr><th>Number</th><th>Count</th><th>Percentage</th><th>First Contact</th><th>Last Contact</th></tr>")
            for contact in stats.top_contacts:
                html.append(f"<tr><td>{contact.number}</td><td>{contact.count}</td>")
                html.append(f"<td>{contact.percentage:.1f}%</td>")
                html.append(f"<td>{contact.first_contact or 'N/A'}</td>")
                html.append(f"<td>{contact.last_contact or 'N/A'}</td></tr>")
            html.append("</table>")
        
        # Duration statistics
        if stats.duration_stats:
            html.append("<h2>Duration Statistics</h2>")
            html.append("<table>")
            html.append("<tr><th>Total</th><th>Average</th><th>Median</th><th>Maximum</th><th>Minimum</th></tr>")
            html.append(f"<tr><td>{stats.duration_stats.total}</td>")
            html.append(f"<td>{stats.duration_stats.average:.1f}</td>")
            html.append(f"<td>{stats.duration_stats.median}</td>")
            html.append(f"<td>{stats.duration_stats.max}</td>")
            html.append(f"<td>{stats.duration_stats.min}</td></tr>")
            html.append("</table>")
        
        # Message type statistics
        if stats.type_stats:
            html.append("<h2>Message Type Statistics</h2>")
            html.append("<table>")
            html.append("<tr><th>Type</th><th>Count</th></tr>")
            for type_name, count in stats.type_stats.types.items():
                html.append(f"<tr><td>{type_name}</td><td>{count}</td></tr>")
            html.append("</table>")
        
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    except Exception as e:
        logger.error(f"Error formatting as HTML: {str(e)}")
        return f"<html><body><p>Error formatting as HTML: {str(e)}</p></body></html>"

def format_as_markdown(stats: BasicStatistics) -> str:
    """Format statistics as Markdown.
    
    Args:
        stats: BasicStatistics object
        
    Returns:
        Markdown string
    """
    if not stats:
        return "# No statistics available"
    
    try:
        md = []
        md.append("# Basic Statistics Summary")
        md.append(f"**Total Records:** {stats.total_records}")
        md.append("")
        
        # Date range
        if stats.date_range:
            md.append("## Date Range")
            md.append("| Attribute | Value |")
            md.append("| --- | --- |")
            md.append(f"| Start Date | {stats.date_range.start} |")
            md.append(f"| End Date | {stats.date_range.end} |")
            md.append(f"| Duration | {stats.date_range.days} days |")
            md.append(f"| Records | {stats.date_range.total_records} |")
            md.append("")
        
        # Top contacts
        if stats.top_contacts:
            md.append("## Top Contacts")
            md.append("| Number | Count | Percentage | First Contact | Last Contact |")
            md.append("| --- | --- | --- | --- | --- |")
            for contact in stats.top_contacts:
                first = contact.first_contact or "N/A"
                last = contact.last_contact or "N/A"
                md.append(f"| {contact.number} | {contact.count} | {contact.percentage:.1f}% | {first} | {last} |")
            md.append("")
        
        # Duration statistics
        if stats.duration_stats:
            md.append("## Duration Statistics")
            md.append("| Metric | Value |")
            md.append("| --- | --- |")
            md.append(f"| Total Duration | {stats.duration_stats.total} |")
            md.append(f"| Average Duration | {stats.duration_stats.average:.1f} |")
            md.append(f"| Median Duration | {stats.duration_stats.median} |")
            md.append(f"| Maximum Duration | {stats.duration_stats.max} |")
            md.append(f"| Minimum Duration | {stats.duration_stats.min} |")
            md.append("")
        
        # Message type statistics
        if stats.type_stats:
            md.append("## Message Type Statistics")
            md.append("| Type | Count |")
            md.append("| --- | --- |")
            for type_name, count in stats.type_stats.types.items():
                md.append(f"| {type_name} | {count} |")
            md.append("")
        
        return "\n".join(md)
    
    except Exception as e:
        logger.error(f"Error formatting as Markdown: {str(e)}")
        return f"# Error\n\nError formatting as Markdown: {str(e)}"

# Dictionary mapping format names to formatter functions
_formatters = {
    'text': format_as_text,
    'json': format_as_json,
    'csv': format_as_csv,
    'html': format_as_html,
    'markdown': format_as_markdown
}

def get_formatter(format_name: str) -> Callable[[BasicStatistics], str]:
    """Get a formatter function by name.
    
    Args:
        format_name: Name of the formatter
        
    Returns:
        Formatter function
        
    Raises:
        ValueError: If the formatter is not found
    """
    if format_name not in _formatters:
        raise ValueError(f"Unknown format: {format_name}. Available formats: {', '.join(_formatters.keys())}")
    
    return _formatters[format_name]

def format_result(stats: BasicStatistics, format_name: str) -> str:
    """Format statistics using the specified formatter.
    
    Args:
        stats: BasicStatistics object
        format_name: Name of the formatter
        
    Returns:
        Formatted string
        
    Raises:
        ValueError: If the formatter is not found
    """
    formatter = get_formatter(format_name)
    return formatter(stats)
