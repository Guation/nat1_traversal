#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["no_dns"]

from .dns_base import dns_base

class no_dns(dns_base):
    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        pass
