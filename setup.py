from setuptools import setup, find_packages

setup(
    name="qakeapi",
    version="0.1.0",
    description="A lightweight ASGI web framework for building fast web APIs with Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Aleksandr",
    author_email="your.email@example.com",
    url="https://github.com/Craxti/qakeapi",
    packages=find_packages(),
    install_requires=[
        "uvicorn",
        "pydantic"
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
) 