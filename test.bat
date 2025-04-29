@echo off
echo Running Python test script...
CD /D C:\Users\thump\Documents\augment-projects\Qlix
python simple_test.py > test_output.txt 2>&1
echo Test completed. Check test_output.txt for results.
pause
