"""
TRD CEA: Health Economic Evaluation Toolkit

A data science toolkit for conducting health economic evaluations comparing 
psychedelic therapies and other interventions for treatment-resistant depression (TRD).
"""

from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the contents of your requirements file
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="trd-cea-toolkit",
    version="0.1.0",
    author="TRD CEA Development Team",
    author_email="trd-cea-dev@example.com",
    description="Health Economic Evaluation Toolkit for Treatment-Resistant Depression Interventions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edithatogo/ee_trd",
    project_urls={
        "Bug Reports": "https://github.com/edithatogo/ee_trd/issues",
        "Source": "https://github.com/edithatogo/ee_trd",
        "Documentation": "https://trd-cea-toolkit.readthedocs.io/",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry", 
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Typing :: Typed"
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["trd_cea", "trd_cea.*"]),
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "trd-cea = trd_cea.cli:main",
            "trd-cea-analyze = trd_cea.cli:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "flake8>=3.8",
            "black>=22.0",
            "mypy>=0.950",
            "jupyter>=1.0",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    keywords=["health-economics", "cost-effectiveness", "psychedelic-therapies", "trd", "cea"],
    license="Apache 2.0",
)