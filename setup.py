#!/usr/bin/env python

from distutils.core import setup

setup(
    name='xd',
    version='0.1.1',
    description='XML Fu',
    author='Daniel Wozniak',
    author_email='dan@woz.io',
    url='https://github.com/dwoz/python-xd',
    packages=['xd'],
    install_requires=[
        'tox',
        'lxml',
    ],
)

