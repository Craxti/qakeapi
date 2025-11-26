"""
Setup script for QakeAPI 1.2.0
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qakeapi",
    version="1.2.0",
    author="QakeAPI Team",
    author_email="",
    description="Revolutionary Hybrid Async/Sync Web Framework for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/craxti/qakeapi",
    packages=find_packages(exclude=["tests", "examples", "*.tests", "*.tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        # Zero dependencies - only standard library!
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
        "server": [
            "uvicorn[standard]>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "qakeapi=qakeapi.cli:main",
        ],
    },
)

