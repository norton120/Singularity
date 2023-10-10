from setuptools import setup, find_packages
from pathlib import Path

setup(
    name='singularity',
    version='0.0.1',
    packages=find_packages(where='src'),
    entry_points = {
        'console_scripts': ['singularity=singlularity.src.cli:main'],
    },
    install_requires=Path('src/requirements.txt').read_text().split('\n'),
)