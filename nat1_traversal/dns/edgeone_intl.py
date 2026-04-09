#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# https://www.tencentcloud.com/zh/document/product/1145/50454
# https://console.tencentcloud.com/api/explorer?Product=teo&Version=2022-09-01

__author__ = "Guation"
__all__ = ["edgeone_intl"]

from logging import debug, info, warning, error
from .edgeone import edgeone

class edgeone_intl(edgeone):
    def request(self, action: str, params: dict = None):
        return self.tencentcloud_request("teo.intl.tencentcloudapi.com", action, "2022-09-01", params)
