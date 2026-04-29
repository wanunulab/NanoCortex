#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Installation script: Install ReRNAFM as a system command
"""
from setuptools import setup, find_packages
import os

# Read README file
readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
long_description = ""
if os.path.exists(readme_file):
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='ReRNAFM',
    version='1.0.0',
    description='RNA-FM model toolkit - for RNA sequence analysis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/ReRNAFM',
    packages=find_packages(),
    py_modules=['main', 'function'],
    entry_points={
        'console_scripts': [
            'ReRNAFM=main:main',
        ],
    },
    install_requires=[
        'torch',
        'numpy',
        'pandas',
        'matplotlib',
        'scikit-learn',
        'biopython',
        'tqdm',
        # Note: RNA-FM package needs to be installed
        # 'fm',  # If the RNA-FM package can be installed via pip
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
