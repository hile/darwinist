
import glob
from setuptools import setup, find_packages
from darwinist import __version__

setup(
    name='darwinist',
    keywords='System Management Utility OS/X Darwin Scripts',
    description='Sysadmin utility modules and scripts for OS/X',
    author='Ilkka Tuohela',
    author_email='hile@iki.fi',
    version=__version__,
    url='https://github.com/hile/darwinist',
    license='PSF',
    scripts=glob.glob('bin/*'),
    packages=find_packages(),
    install_requires=(
        'systematic>=4.8.3',
        'appscript',
    ),
)
