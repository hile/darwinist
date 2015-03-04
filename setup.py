#!/usr/bin/env python
"""
Scripts and system tool wrappers for OS/X

This module is split from darwinist module to platform dependent tool
"""

import glob
from setuptools import setup, find_packages

VERSION='4.1.1'

setup(
    name = 'darwinist',
    keywords = 'System Management Utility OS/X Darwin Scripts',
    description = 'Sysadmin utility modules and scripts for OS/X',
    author = 'Ilkka Tuohela',
    author_email = 'hile@iki.fi',
    version = VERSION,
    url = 'https://github.com/hile/darwinist',
    license = 'PSF',
    scripts = glob.glob('bin/*'),
    packages = find_packages(),
    install_requires = (
        'systematic>=4.0.2',
        'appscript',
        'pyfsevents'
    ),
)

