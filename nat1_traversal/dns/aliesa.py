#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["aliesa"]

from logging import debug, info, warning, error
from .alicloud_common import alicloud_common

class aliesa(alicloud_common):
    def request(self, method: str, action: str, params: dict = None):
        return self.alicloud_rpc_request(method, "esa.cn-hangzhou.aliyuncs.com", action, "2024-09-10", params)

    def search_siteid(self, domain: str) -> int:
        domainPunycode = self.domain2punycode(domain)
        for i in self.request("GET", "ListSites", {})["Sites"]:
            if self.domain2punycode(i["SiteName"]) == domainPunycode:
                return i["SiteId"]
        raise ValueError(
            "无法搜索到域名%s" % domain
        )

    def search_recordid(self, sub_domain: str, siteid: int) -> int:
        domainPunycode = self.domain2punycode(sub_domain)
        params = {
            "SiteId": siteid,
            "PageSize": 500
        }
        for i in self.request("GET", "ListRecords", params)["Records"]:
            if self.domain2punycode(i["RecordName"]) == domainPunycode:
                return i["RecordId"]
        raise ValueError(
            "无法搜索到前缀%s" % sub_domain
        )

    def search_configid(self, sub_domain: str, siteid: int) -> int:
        domainPunycode = self.domain2punycode(sub_domain)
        params = {
            "SiteId": siteid,
            "PageSize": 500
        }
        for i in self.request("GET", "ListOriginRules", params)["Configs"]:
            if self.domain2punycode(i.get("RuleName", "")) == domainPunycode:
                return i["ConfigId"]
        raise ValueError(
            "无法搜索到前缀%s" % sub_domain
        )

    def update_ip(self, sub_domain: str, domain: str, ip: str):
        siteid = self.search_siteid(domain)
        recordid = self.search_recordid(f"{sub_domain}.{domain}", siteid)
        payload = {
            "RecordId": recordid,
            "Data": '{"Value":"' + ip + '"}'
        }
        return self.request("POST", "UpdateRecord", payload)

    def update_port(self, sub_domain: str, domain: str, port: int):
        siteid = self.search_siteid(domain)
        configid = self.search_configid(sub_domain, siteid)
        payload = {
            "SiteId": siteid,
            "ConfigId": configid,
            "OriginHttpPort": port,
            "OriginHttpsPort": port
        }
        return self.request("POST", "UpdateOriginRule", payload)

    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        if srv_prefix != "_web._tcp.":
            raise ValueError(
                "esa平台只支持type为web"
            )
        self.update_ip(sub_domain, domain, ip)
        self.update_port(sub_domain, domain, port)
