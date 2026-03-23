#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

from setuptools import setup
import pathlib

VERSION = None

exec(pathlib.Path(__file__).parent.joinpath("nat1_traversal/util/version.py").read_text())

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
    install_requires=[x.strip() for x in pathlib.Path(__file__).parent.joinpath("requirements.txt").read_text().splitlines()],
    project_urls={
        "url": "https://github.com/Guation/nat1_traversal",
    }
)