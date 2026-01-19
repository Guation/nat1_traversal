#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["webhook"]

import requests, json
from nat1_traversal.dns.dns_base import dns_base
from logging import debug, info, warning, error

class webhook(dns_base):
    def __init__(self, id, token):
        super().__init__(id, token)
        self.url = self.id

    def request(self, method: str, params: dict = None):
        headers = {
            "Content-type": "application/json",
            "User-Agent": self.USER_AGENT,
        }
        if self.token is not None:
            headers["Authorization"] = "Bearer " + self.token
        debug("method=%s, url=%s, params=%s, headers=%s", method, self.url, params, headers)
        try:
            response = requests.request(method, self.url, json=params, headers=headers)
            r = response.content
            if response.status_code != 200:
                raise ValueError(
                    '服务器拒绝了请求：url=%s, status_code=%d, response=%s' % (self.url, response.status_code, r)
                )
            else:
                j = json.loads(r)
                debug("url=%s, response=%s", self.url, j)
                return j
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                "%s 请求失败" % self.url
            ) from e

    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        payload = {
            "srv_prefix": srv_prefix,
            "sub_domain": sub_domain,
            "domain": domain,
            "ip": ip,
            "port": port
        }
        self.request("POST", payload)
