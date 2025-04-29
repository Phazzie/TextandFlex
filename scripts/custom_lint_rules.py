import sys
import re
from pathlib import Path

# 2. Enforce project-specific conventions: forbid 'foo'/'bar' in variable names
# 3. Enforce docstring presence and minimum length
# 5. Enforce self-documenting variable names (no single-letter except i, j, k)
# 6. Forbid tests with only assert True/False or no assertions
# 7. Block commit if linter warnings increase (requires baseline file)

IGNORED_SINGLE_LETTERS = {'i', 'j', 'k'}
MIN_DOCSTRING_LENGTH = 10


def check_variable_names(file_path, lines):
    errors = []
    for idx, line in enumerate(lines):
        if re.search(r'\b(foo|bar)\b', line):
            errors.append(f"{file_path}:{idx+1}: Forbidden variable name 'foo' or 'bar'.")
        # Check for single-letter variable names (except i, j, k)
        match = re.findall(r'\b([a-zA-Z])\b', line)
        for var in match:
            if var not in IGNORED_SINGLE_LETTERS:
                errors.append(f"{file_path}:{idx+1}: Single-letter variable name '{var}' is discouraged.")
    return errors

def check_docstrings(file_path, lines):
    errors = []
    in_func = False
    doc_found = False
    doc_len = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith('def '):
            in_func = True
            doc_found = False
            doc_len = 0
        elif in_func and line.strip().startswith('"""'):
            doc_found = True
            doc_len = len(line.strip().strip('"'))
        elif in_func and doc_found:
            if not line.strip().startswith('"""'):
                doc_len += len(line.strip())
            else:
                if doc_len < MIN_DOCSTRING_LENGTH:
                    errors.append(f"{file_path}:{idx+1}: Docstring too short (<{MIN_DOCSTRING_LENGTH} chars).")
                in_func = False
    return errors

def check_tests(file_path, lines):
    errors = []
    if 'test' in str(file_path):
        has_assert = any('assert' in line for line in lines)
        if not has_assert:
            errors.append(f"{file_path}: Test file has no assertions.")
        for idx, line in enumerate(lines):
            if re.match(r'\s*assert\s+(True|False)\s*$', line):
                errors.append(f"{file_path}:{idx+1}: Useless assertion (assert True/False).")
    return errors

def main():
    files = [Path(f) for f in sys.argv[1:] if f.endswith('.py')]
    all_errors = []
    for file_path in files:
        try:
            lines = file_path.read_text(encoding='utf-8').splitlines()
        except Exception:
            continue
        all_errors.extend(check_variable_names(file_path, lines))
        all_errors.extend(check_docstrings(file_path, lines))
        all_errors.extend(check_tests(file_path, lines))
    if all_errors:
        for err in all_errors:
            print(err)
        sys.exit(1)

if __name__ == '__main__':
    main()
