#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["dns_base"]

from nat1_traversal.util.version import VERSION
from abc import ABC, abstractmethod

class dns_base(ABC):
    USER_AGENT = f"NAT1 Traversal/{VERSION} (Guation@guation.cn)"
    def __init__(self, id: str, token: str):
        self.id: str = id
        self.token: str = token

    @staticmethod
    def domain2punycode(domain: str):
        return domain.encode('idna').decode('ascii')

    @abstractmethod
    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        pass
