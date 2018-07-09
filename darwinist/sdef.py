"""
Module to create application dictionaries for appscript using command line sdef tool
"""

import os
from subprocess import check_output
from lxml import etree as ET


class SDEFError(Exception):
    pass


class SDEF(object):
    def __init__(self, path):
        self.path = path
        if not os.path.isdir(path):
            raise SDEFError('Not a directory: {0}'.format(path))
        self.tree = ET.fromstring(check_output(['sdef', path]))

    def __getattr__(self, attr):
        if attr == 'terms':
            return self.__generate_terms()

    def __generate_terms(self):
        output = 'version = 1.1\npath = {0}'.format(self.path)
        classes = []
        enums = []
        properties = []
        elements = []
        commands = []
        for suite in self.tree.xpath('suite'):
            for node in suite.xpath('class'):
                name = node.get('name').replace(' ', '_')
                code = node.get('code')
                classes.append((name, code))
                if node.get('inherits') is None:
                    continue
                element = node.get('plural').replace('  _')
                elements.append((element, code))

            for node in suite.xpath('enumeration/enumerator'):
                name = node.get('name').replace(' ', '_')
                code = node.get('code')
                enums.append((name, code))

            for node in suite.xpath('class/property'):
                name = node.get('name').replace(' ', '_')
                code = node.get('code')
                properties.append((name, code))

            for node in suite.xpath('command'):
                name = node.get('name').replace(' ', '_')
                code = node.get('code')
                cparams = []
                for p in node.xpath('parameter'):
                    pname = p.get('name').replace(' ', '_')
                    pcode = p.get('code')
                    cparams.append((pname, pcode))
                commands.append((name, code, cparams))

        output += '\nclasses = {0}'.format(classes)
        output += '\nenums = {0}'.format(enums)
        output += '\nproperties = {0}'.format(properties)
        output += '\nelements = {0}'.format(elements)
        output += '\ncommands = {0)}'.format(commands)

        return output
