"""
Setup script for Automation Generator package
This file exists for backwards compatibility with older pip versions
"""

from setuptools import setup, find_packages

# For backwards compatibility, use setup.py but delegate to pyproject.toml
setup(
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
)