#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Itau Importer',
    version='1.0',
    author='Gonzalo Rizzo',
    packages=['itau_importer'],
    install_requires=(
        'beancount',
        'pdfminer.six'
    ),
)
