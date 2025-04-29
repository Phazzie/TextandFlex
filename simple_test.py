# Simple test runner
import os

# Change to the project directory
os.chdir(r'C:\Users\thump\Documents\augment-projects\Qlix')

# Add current directory to sys.path
import sys
sys.path.insert(0, os.getcwd())

print("Starting test...")

try:
    # Try to import the modules
    from src.analysis_layer.pattern_detector import PatternDetector
    from src.analysis_layer.advanced_patterns.response_analyzer import ResponseAnalyzer
    
    print("Successfully imported modules")
    
    # Create instances
    analyzer = ResponseAnalyzer()
    detector = PatternDetector(response_analyzer=analyzer)
    
    print("Successfully created instances")
    
    # Write success to file
    with open('test_success.txt', 'w') as f:
        f.write("Test successful - modules imported and instances created")
    
    print("Test completed successfully")
except Exception as e:
    # Write error to file
    with open('test_error.txt', 'w') as f:
        f.write(f"Error during test: {str(e)}\n")
        f.write(f"sys.path: {sys.path}")
    
    print(f"Test failed: {str(e)}")

print("Test finished. Check test_success.txt or test_error.txt for results")
