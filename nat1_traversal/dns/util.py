#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["USER_AGENT", "domain2punycode"]

from nat1_traversal.util.version import VERSION

USER_AGENT = f"NAT1 Traversal/{VERSION} (Guation@guation.cn)"

def domain2punycode(domain: str):
    return domain.encode('idna').decode('ascii')
