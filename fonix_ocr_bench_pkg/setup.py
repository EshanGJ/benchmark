from setuptools import setup, find_packages

# This file is kept for backward compatibility
# All configuration is in pyproject.toml
setup(
    packages=find_packages(exclude=["tests*", "data*", "results*"]),
)
