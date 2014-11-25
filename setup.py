#!/usr/bin/env python
"""
Scripts and system tool wrappers for OS/X

This module is split from darwinist module to platform dependent tool
"""

import sys,os,glob
from setuptools import setup

VERSION='4.1.0'

setup(
    name = 'darwinist',
    keywords = 'System Management Utility OS/X Darwin Scripts',
    description = 'Sysadmin utility modules and scripts for OS/X',
    author = 'Ilkka Tuohela',
    author_email = 'hile@iki.fi',
    version = VERSION,
    url = 'http://tuohela.net/packages/darwinist',
    license = 'PSF',
    scripts = glob.glob('bin/*'),
    packages = (
        'darwinist',
    ),
    install_requires = (
        'systematic>=4.0.2',
        'appscript',
        'pyfsevents'
    ),
)

