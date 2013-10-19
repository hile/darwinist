#!/usr/bin/env python
"""
Wrapper for scons build systems to install dependencies from homebrew
build system on OS/X.

This is only meant to allow automatic tool installs and not at all to
replace or replicate all functionality of direct use of brew command.

Example usage:
brew = Homebrew()

# Example how to list installed packages
for package in brew.values():
    print package.name, package.versions

# Example how to list available packages
for name in brew.available_formulas():
    print name

# Example how to update homebrew system
brew.update()
brew.upgrade_all()
brew.cleanup()

# Example how to install packages
for arg in sys.argv[1:]:
    try:
        brew.install(arg)
    except HomebrewError,emsg:
        print emsg

"""

import os
from subprocess import Popen, PIPE

HOMEBREW_PREFIX = '/usr/local'
HOMEBREW_FORMULAS = os.path.join(HOMEBREW_PREFIX, 'Library', 'Formula')
HOMEBREW_DEFAULT_COMMAND = os.path.join(HOMEBREW_PREFIX, 'bin', 'brew')

class HomebrewError(Exception):
    pass

class Homebrew(dict):
    """
    Wrapper for homebrew packaging system's brew command
    """
    def __init__(self, brew=HOMEBREW_DEFAULT_COMMAND):
        self.brew = brew
        self.update_installed()

    def keys(self):
        """
        Return package names as sorted list
        """
        return sorted(dict.keys(self))

    def items(self):
        """
        Return name, package as sorted by name with self.keys()
        """
        return [(k, self[k]) for k in self.keys()]

    def values(self):
        """
        Return packages as sorted by name with self.keys()
        """
        return [self[k] for k in self.keys()]

    def update_installed(self):
        """
        Update our list of installed homebrew package names
        """
        self.clear()
        cmd = [self.brew, 'list']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        for l in filter(lambda x: x.strip()!='',  stdout.split('\n')):
            self[l] = HomebrewPackage(self, l)

    def available_formulas(self):
        """
        List available packages with Homebrew formula
        """
        return [os.path.splitext(x)[0] for x in filter(lambda x:
            x[-3:]=='.rb', os.listdir(HOMEBREW_FORMULAS)
        )]

    def cleanup(self):
        """
        Run brew clean to remove stale files
        """
        cmd = [self.brew, 'cleanup']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode != 0:
            raise HomebrewError('Error cleaning up homebrew: %s' % stderr)
        return stdout

    #noinspection PyMethodOverriding
    def update(self):
        """
        Update homebrew package descriptions with brew update
        """
        cmd = [self.brew, 'update']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode != 0:
            raise HomebrewError('Error updating homebrew\n%s' % stdout)
        return stdout

    def upgrade_all(self):
        """
        Run brew upgrade --all to upgrade installed packages. Running
        self.cleanup() afterwards is recommended to get rid of old versions.
        """
        cmd = [self.brew, 'upgrade', '--all']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode != 0:
            raise HomebrewError('Error upgrading brew packages\n%s' % stdout)
        return stdout

    def is_installed(self, package):
        """
        Returns if package is installed,  at least some version
        """
        return package in self.keys()

    def install(self, package, force_install=False):
        """
        Install package if formula is available
        """
        if not force_install and self.is_installed(package):
            return
        if not package in self.available_formulas():
            raise HomebrewError('Homebrew: unknown package: %s' % package)

        package = HomebrewPackage(self, package)
        package.install()
        self[package.name] = package

class HomebrewPackage(object):
    """
    Abstraction for one homebrew package, with multiple possible versions
    """
    def __init__(self, brew, name):
        self.brew = brew
        self.name = name
        self.cellar = os.path.join(HOMEBREW_PREFIX, 'Cellar', name)

    def __repr__(self):
        return '%s in %s' % (self.name, self.cellar)

    def __getattr__(self, attr):
        if attr == 'versions':
            return os.listdir(self.cellar)

        raise AttributeError('No such HomebrewPackage attribute: %s' % attr)

    def install(self, force_install=False):
        """
        Install a package from homebrew
        """
        if os.path.isdir(self.cellar) and not force_install:
            return

        cmd = [self.brew.brew, 'install', self.name]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = p.communicate()

        if p.returncode != 0:
            raise HomebrewError('Homebrew: error installing %s\n%s' % (self.name, stdout))

        return stdout, stderr
