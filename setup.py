#!/usr/bin/env python3
"""
Setup configuration for DigitalAuditor Cleshnya
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="digital-auditor",
    version="1.0.0",
    description="AI-powered audit system following CISA/CIA standards",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Digital Auditor Team",
    url="https://github.com/your-org/DigitalAuditor_Cleshnya",
    packages=find_packages(exclude=["tests", "docs", "scripts"]),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "ollama>=0.4.0",
        "langchain>=0.3.0",
        "langchain-community>=0.3.0",
        "chromadb>=0.5.0",
        "sentence-transformers>=2.2.0",
        "faiss-cpu>=1.8.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "tavily-python>=0.3.0",
        "duckduckgo-search>=6.0.0",
        "pypdf>=4.0.0",
        "python-docx>=1.1.0",
        "markdown>=3.5.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "digital-auditor=main:cli",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
