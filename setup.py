#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

from setuptools import setup, find_packages

setup(
    name='nat1_traversal',
    version='1.0.2',
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
    ],
    project_urls={
        "url": "https://github.com/Guation/nat1_traversal",
    }
)