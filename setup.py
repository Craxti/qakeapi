"""
Setup configuration for QakeAPI framework.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qakeapi",
    version="1.1.0",
    description="Modern asynchronous web framework for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="QakeAPI Team",
    author_email="team@qakeapi.dev",
    url="https://github.com/qakeapi/qakeapi",
    packages=find_packages(exclude=["tests", "examples"]),
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Framework :: AsyncIO",
    ],
    keywords="web framework api rest async asgi",
    project_urls={
        "Documentation": "https://github.com/qakeapi/qakeapi",
        "Source": "https://github.com/qakeapi/qakeapi",
        "Tracker": "https://github.com/qakeapi/qakeapi/issues",
    },
)
