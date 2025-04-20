"""
Setup script for the Phone Records Analyzer package.
"""
from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read long description from README
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="phone_records_analyzer",
    version="0.1.0",
    description="A tool for analyzing phone communication records",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Phone Records Analyzer Team",
    author_email="example@example.com",
    url="https://github.com/yourusername/phone-records-analyzer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "phone-analyzer=src.app:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
