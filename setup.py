#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

from setuptools import setup, find_packages
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
    install_requires=[
        "urllib3==2.2.3",
        "requests",
        "dnspython",
        "tencentcloud-sdk-python-dnspod",
        "alibabacloud_alidns20150109",
    ],
    project_urls={
        "url": "https://github.com/Guation/nat1_traversal",
    }
)