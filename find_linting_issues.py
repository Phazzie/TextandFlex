#!/usr/bin/env python
"""
Simple script to identify common coding style issues in the project.
"""

import os
import re
from pathlib import Path

# Common linting issues to check for
ISSUES = {
    "E1: Line too long": (r'.{100,}', "Line exceeds 99 characters"),
    "E2: Missing docstring": (r'^\s*def [^_].*\):\s*$', "Function missing docstring"),
    "E3: Unused import": (r'import (\w+).*?(?!.*\1)', "Unused import"),
    "E4: Trailing whitespace": (r'[ \t]+$', "Line has trailing whitespace"),
    "E5: Missing type hint": (r'def [^_].*\)(?! ->):', "Function missing return type hint"),
    "E6: TODO comment": (r'#.*TODO', "TODO comment in code"),
    "E7: Print statement": (r'(?<![\'"])print\s*\(', "Print statement in production code"),
    "E8: Explicit None compare": (r'== None|None ==|!= None|None !=', "Use 'is None' or 'is not None' instead"),
    "E9: Inconsistent quotes": (r'"(?:[^"\\]|\\.)*".*\'(?:[^\'\\]|\\.)*\'', "Mixed quote styles in same file"),
    "E10: Bare except": (r'except\s*:', "Bare except clause"),
}

def check_file(file_path):
    """Check a file for common linting issues."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return [f"Error reading file: {e}"]
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check each pattern
        for issue_name, (pattern, message) in ISSUES.items():
            if re.search(pattern, line):
                issues.append((issue_name, line_num, message, line.strip()))
    
    # Check docstring pattern across multiple lines
    has_docstring = False
    for i, line in enumerate(lines):
        if i > 0 and 'def ' in lines[i-1] and '"""' in line:
            has_docstring = True
            break
    
    if 'def ' in ''.join(lines) and not has_docstring:
        issues.append(("E2: Missing docstring", 0, "No docstring found for functions", ""))
    
    return issues

def scan_directory(directory):
    """Scan a directory for Python files with linting issues."""
    all_issues = {}
    stats = {issue_name: 0 for issue_name in ISSUES.keys()}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                issues = check_file(file_path)
                
                if issues:
                    all_issues[file_path] = issues
                    for issue_name, _, _, _ in issues:
                        stats[issue_name] = stats.get(issue_name, 0) + 1
    
    return all_issues, stats

def main():
    """Main function to run the analysis."""
    # Set the project directory
    project_dir = Path(__file__).parent
    src_dir = project_dir / 'src'
    
    # Check if the src directory exists
    if not src_dir.exists():
        print(f"src directory not found at {src_dir}")
        return
    
    print(f"Scanning directory: {src_dir}")
    
    # Scan the directory
    all_issues, stats = scan_directory(src_dir)
    
    # Write results to a file
    with open('linting_issues.txt', 'w') as f:
        f.write("# Linting Issues Found\n\n")
        
        # Write stats
        f.write("## Statistics\n\n")
        total_issues = sum(len(issues) for issues in all_issues.values())
        f.write(f"Total issues found: {total_issues}\n")
        f.write(f"Files with issues: {len(all_issues)}\n\n")
        
        f.write("## Issues by type:\n\n")
        for issue_name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                f.write(f"- {issue_name}: {count} occurrences\n")
        
        f.write("\n## Issues by file:\n\n")
        for file_path, issues in all_issues.items():
            rel_path = os.path.relpath(file_path, project_dir)
            f.write(f"### {rel_path} ({len(issues)} issues)\n\n")
            
            for issue_name, line_num, message, line_content in issues:
                if line_num > 0:
                    f.write(f"- Line {line_num}: {issue_name} - {message}\n")
                    if line_content:
                        f.write(f"  ```python\n  {line_content}\n  ```\n")
                else:
                    f.write(f"- {issue_name} - {message}\n")
            
            f.write("\n")
    
    print(f"Analysis complete. Results saved to linting_issues.txt")

if __name__ == "__main__":
    main()
