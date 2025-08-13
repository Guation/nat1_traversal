#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

from setuptools import setup, find_packages
import pathlib

VERSION = None

with open(pathlib.Path(__file__).parent.joinpath("nat1_traversal/util/version.py")) as f:
    exec(f.read())

setup(
    name='nat1_traversal',
    version=VERSION,
    author="Guation",
    packages=['nat1_traversal', 'nat1_traversal.dns', 'nat1_traversal.util'],
    entry_points={
        'console_scripts': [
            'nat1_traversal = nat1_traversal.nat1_traversal:main'
        ]
    },
    include_package_data=True,
    install_requires=[
        "requests",
        "dnspython",
    ],
    project_urls={
        "url": "https://github.com/Guation/nat1_traversal",
    }
)