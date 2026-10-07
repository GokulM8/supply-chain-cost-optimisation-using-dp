"""
Setup script for Supply Chain Cost Optimization Engine.

This is a fallback for older pip versions that don't support pyproject.toml.
Modern installations should use `pip install -e .` with pyproject.toml.
"""

from setuptools import setup, find_packages
import os

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="supply-chain-cost-optimization-engine",
    version="1.0.0",
    description="A Dynamic Programming based supply chain optimization system that computes the globally lowest-cost production, transportation, and inventory plan over a finite planning horizon.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Supply Chain Optimization Team",
    author_email="contact@example.com",
    url="https://github.com/example/supply-chain-cost-optimizer",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Logistics",
        "Topic :: Scientific/Engineering :: Optimization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Business :: Logistics",
        "Topic :: Finance :: Accounting",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "supply-chain-optimize = engine.dp:main",
        ],
    },
    project_urls={
        "Bug Tracker": "https://github.com/example/supply-chain-cost-optimizer/issues",
        "Documentation": "https://supply-chain-optimizer.readthedocs.io/",
        "Source Code": "https://github.com/example/supply-chain-cost-optimizer",
    },
)