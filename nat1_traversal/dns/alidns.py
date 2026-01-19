#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["alidns"]

from logging import debug, info, warning, error
from .alicloud_common import alicloud_common

class alidns(alicloud_common):
    def request(self, action: str, params: dict = None):
        return self.alicloud_rpc_request("POST", "alidns.aliyuncs.com", action, "2015-01-09", params)

    def search_recordid(self, sub_domain: str, domain: str) -> str:
        domainPunycode = self.domain2punycode(sub_domain)
        params = {
            "DomainName": domain,
            "PageSize": 500
        }
        for i in self.request("DescribeDomainRecords", params)["DomainRecords"]["Record"]:
            if self.domain2punycode(i["RR"]) == domainPunycode:
                return i["RecordId"]
        debug("无法搜索到前缀%s", sub_domain)
        return None

    def update_record(self, sub_domain: str, domain: str, record_type: str, value: str, /, **params):
        if record_type not in ["A", "SRV"]:
            raise ValueError(
                "不支持记录类型%s" % record_type
            )
        payload = {
            "DomainName": domain,
            "RR": sub_domain,
            "Type": record_type,
            "Value": value if record_type == "A" else f'{params.get("priority", 10)} {params.get("weight", 0)} {params["port"]} {value}'
        }
        recordid = self.search_recordid(sub_domain, domain)
        if recordid is None: # 新建
            return self.request("AddDomainRecord", params)
        else: # 更新
            payload["RecordId"] = recordid
            return self.request("UpdateDomainRecord", params)

    def update_record_simple(self, srv_prefix: str, sub_domain: str, domain: str, ip: str, port: int):
        self.update_record(sub_domain, domain, "A", ip)
        self.update_record(srv_prefix + sub_domain, domain, "SRV", f"{sub_domain},{domain}", port=port)
