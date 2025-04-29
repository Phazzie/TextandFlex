@echo off
echo Running ResponseAnalyzer Integration Tests...
cd /d C:\Users\thump\Documents\augment-projects\Qlix
python response_analyzer_tests.py
echo.
if %errorlevel% equ 0 (
    echo SUCCESS: All tests passed!
) else (
    echo ERROR: Some tests failed!
)
pause
