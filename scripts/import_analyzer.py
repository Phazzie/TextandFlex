"""
Import Analyzer
--------------
Script to analyze Python file imports and create a visualization of file relationships.
"""

import os
import re
import json
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

# Regular expression to match Python imports
IMPORT_PATTERN = re.compile(r'^\s*(?:from|import)\s+([.\w]+)')
RELATIVE_IMPORT_PATTERN = re.compile(r'^\s*from\s+(\.*\w+(?:\.\w+)*)\s+import')

def find_python_files(root_dir):
    """Find all Python files in the directory tree."""
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                yield os.path.join(root, file)

def parse_imports(file_path):
    """Parse imports from a Python file."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Check for import statements
                match = IMPORT_PATTERN.match(line)
                if match:
                    imported_module = match.group(1)
                    imports.append(imported_module)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return imports

def resolve_relative_import(importing_file, relative_import):
    """Resolve a relative import to an absolute path."""
    # Convert file path to module path
    base_dir = os.path.dirname(os.path.abspath(importing_file))
    
    # Handle dot notation (each dot means go up one directory)
    dot_count = 0
    module_path = relative_import
    
    if relative_import.startswith('.'):
        parts = relative_import.split('.')
        for part in parts:
            if part == '':
                dot_count += 1
            else:
                break
        
        # Remove the dots from the import
        module_path = relative_import[dot_count:]
        
        # Go up dot_count directories
        for _ in range(dot_count):
            base_dir = os.path.dirname(base_dir)
    
    if module_path:
        return os.path.join(base_dir, *module_path.split('.'))
    else:
        return base_dir

def create_import_graph(root_dir):
    """Create a graph of file dependencies."""
    # Map of file to its imports
    dependencies = defaultdict(list)
    # Map of module names to file paths
    module_map = {}
    
    # First pass: collect all Python files and map module names to file paths
    for file_path in find_python_files(root_dir):
        # Create module name from file path (relative to root_dir)
        rel_path = os.path.relpath(file_path, root_dir)
        module_name = os.path.splitext(rel_path)[0].replace(os.sep, '.')
        module_map[module_name] = file_path
        
        # Also map the directory as a package if __init__.py exists
        dir_path = os.path.dirname(file_path)
        while dir_path and dir_path != root_dir:
            init_py = os.path.join(dir_path, '__init__.py')
            if os.path.exists(init_py):
                package_path = os.path.relpath(dir_path, root_dir).replace(os.sep, '.')
                if package_path:
                    module_map[package_path] = dir_path
            dir_path = os.path.dirname(dir_path)
    
    # Second pass: analyze imports
    for file_path in find_python_files(root_dir):
        rel_path = os.path.relpath(file_path, root_dir)
        imports = parse_imports(file_path)
        
        for imported in imports:
            # Try to find the imported module in our module map
            if imported in module_map:
                dependencies[rel_path].append(os.path.relpath(module_map[imported], root_dir))
            else:
                # It might be a relative import or external library
                if imported.startswith('.'):
                    resolved = resolve_relative_import(file_path, imported)
                    if os.path.exists(resolved + '.py'):
                        dependencies[rel_path].append(os.path.relpath(resolved + '.py', root_dir))
                    elif os.path.exists(os.path.join(resolved, '__init__.py')):
                        dependencies[rel_path].append(os.path.relpath(os.path.join(resolved, '__init__.py'), root_dir))
    
    return dependencies

def save_dependency_json(dependencies, output_file):
    """Save dependencies to a JSON file."""
    with open(output_file, 'w') as f:
        json.dump(dependencies, f, indent=2)

def visualize_dependencies(dependencies, output_file):
    """Create a graph visualization of dependencies."""
    G = nx.DiGraph()
    
    # Add nodes and edges
    for file, imports in dependencies.items():
        if not G.has_node(file):
            G.add_node(file)
        
        for imported in imports:
            if not G.has_node(imported):
                G.add_node(imported)
            G.add_edge(file, imported)
    
    # Draw the graph
    plt.figure(figsize=(20, 20))
    pos = nx.spring_layout(G, k=0.8)
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='lightblue', 
            font_size=8, font_weight='bold', arrows=True)
    plt.savefig(output_file, format="PNG", dpi=300)
    plt.close()

if __name__ == "__main__":
    # Define root directory to analyze (the src folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(os.path.dirname(script_dir), "src")
    
    print(f"Analyzing imports in {root_dir}...")
    dependencies = create_import_graph(root_dir)
    
    # Save dependencies as JSON
    json_output = os.path.join(os.path.dirname(script_dir), "dependency_map.json")
    save_dependency_json(dependencies, json_output)
    print(f"Dependency map saved to {json_output}")
    
    # Create visualization
    try:
        viz_output = os.path.join(os.path.dirname(script_dir), "dependency_graph.png")
        visualize_dependencies(dependencies, viz_output)
        print(f"Dependency visualization saved to {viz_output}")
    except Exception as e:
        print(f"Couldn't create visualization: {e}")
        print("You may need to install networkx and matplotlib: pip install networkx matplotlib")
