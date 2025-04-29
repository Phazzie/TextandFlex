#!/usr/bin/env python
"""
Script to analyze and categorize linting errors in the codebase.
"""
import os
import re
import subprocess
import json
from collections import Counter, defaultdict

def run_ruff_check(file_path):
    """Run ruff check on a file and return the output."""
    try:
        result = subprocess.run(
            ["python", "-m", "ruff", "check", file_path, "--format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return []
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # If not JSON, try to parse the text output
            errors = []
            for line in result.stdout.splitlines():
                if ":" in line:
                    parts = line.split(":", 3)
                    if len(parts) >= 3:
                        errors.append({
                            "file_path": parts[0],
                            "line": parts[1],
                            "code": parts[2].strip(),
                            "message": parts[3] if len(parts) > 3 else ""
                        })
            return errors
    except Exception as e:
        print(f"Error running ruff check: {e}")
        return []

def find_python_files(directory):
    """Find all Python files in the directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def analyze_linting_errors(python_files):
    """Analyze linting errors in the Python files."""
    all_errors = []
    error_counts = Counter()
    error_by_file = defaultdict(list)
    
    for file_path in python_files:
        errors = run_ruff_check(file_path)
        if errors:
            all_errors.extend(errors)
            for error in errors:
                code = error.get("code", "unknown")
                error_counts[code] += 1
                error_by_file[file_path].append(error)
    
    return {
        "all_errors": all_errors,
        "error_counts": error_counts,
        "error_by_file": error_by_file,
        "total_errors": len(all_errors),
        "total_files_with_errors": len(error_by_file)
    }

def save_results(results, output_file="linting_analysis.txt"):
    """Save analysis results to a file."""
    with open(output_file, "w") as f:
        f.write("# Linting Error Analysis\n\n")
        
        f.write(f"Total errors found: {results['total_errors']}\n")
        f.write(f"Files with errors: {results['total_files_with_errors']}\n\n")
        
        f.write("## Error types by frequency:\n\n")
        for code, count in results["error_counts"].most_common():
            f.write(f"- {code}: {count} occurrences\n")
        
        f.write("\n## Files with the most errors:\n\n")
        file_error_counts = [(file, len(errors)) for file, errors in results["error_by_file"].items()]
        file_error_counts.sort(key=lambda x: x[1], reverse=True)
        
        for file, count in file_error_counts[:10]:  # Top 10 files
            f.write(f"- {file}: {count} errors\n")
        
        # Sample of the most common errors
        f.write("\n## Examples of common errors:\n\n")
        for code, count in results["error_counts"].most_common(5):
            f.write(f"### {code} ({count} occurrences):\n")
            for error in results["all_errors"]:
                if error.get("code") == code:
                    f.write(f"- {error.get('file_path')}:{error.get('line')}: {error.get('message', '')}\n")
                    break
            f.write("\n")

def main():
    """Main function to run the analysis."""
    project_dir = os.path.abspath(os.getcwd())
    print(f"Analyzing Python files in {project_dir}...")
    
    python_files = find_python_files(os.path.join(project_dir, "src"))
    print(f"Found {len(python_files)} Python files.")
    
    print("Running linting analysis...")
    results = analyze_linting_errors(python_files)
    
    output_file = "linting_analysis.txt"
    save_results(results, output_file)
    print(f"Analysis saved to {output_file}")

if __name__ == "__main__":
    main()
