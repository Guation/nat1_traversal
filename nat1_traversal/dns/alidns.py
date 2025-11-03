#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["update_record", "init"]

from alibabacloud_tea_openapi.client import Client as OpenApiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_openapi_util.client import Client as OpenApiUtilClient
from alibabacloud_tea_openapi.exceptions import AlibabaCloudException
from logging import debug, info, warning, error
from .util import USER_AGENT, domain2punycode

__id: str = None
__token: str = None

def init(id: str, token: str):
    global __id, __token
    __id = id
    __token = token

def request(action: str, params: dict = None):
    client = OpenApiClient(open_api_models.Config(
        type='access_key',
        access_key_id = __id,
        access_key_secret = __token,
        endpoint = f'alidns.aliyuncs.com',
        user_agent = USER_AGENT
    ))
    models_params = open_api_models.Params(
        action=action,
        version='2015-01-09',
        protocol='HTTPS',
        method='POST',
        auth_type='AK',
        style='RPC',
        pathname=f'/',
        req_body_type='json',
        body_type='json'
    )
    runtime = util_models.RuntimeOptions()
    request = open_api_models.OpenApiRequest(
        query=OpenApiUtilClient.query(params)
    )
    try:
        return client.call_api(models_params, request, runtime)["body"]
    except AlibabaCloudException as e:
        raise ValueError(
            "%s 请求失败" % action
        ) from e

def search_recordid(sub_domain: str, domain: str) -> str:
    domainPunycode = domain2punycode(sub_domain)
    params = {
        "DomainName": domain,
        "PageSize": 500
    }
    for i in request("DescribeDomainRecords", params)["DomainRecords"]["Record"]:
        if domain2punycode(i["RR"]) == domainPunycode:
            return i["RecordId"]
    debug("无法搜索到前缀%s", sub_domain)
    return None

def update_record(sub_domain: str, domain: str, record_type: str, value: str, /, **params):
    if record_type not in ["A", "SRV"]:
        raise ValueError(
            "不支持记录类型%s" % record_type
        )
    payload = {
        "DomainName": domain,
        "RR": sub_domain,
        "Type": record_type,
    }
    if record_type == "A":
        payload["Value"] = value
    elif record_type == "SRV":
        payload["Value"] = f'{params.get("priority", 10)} {params.get("weight", 0)} {params["port"]} {value}.{domain}'
    recordid = search_recordid(sub_domain, domain)
    if recordid is None: # 新建
        return request("AddDomainRecord", params)
    else: # 更新
        payload["RecordId"] = recordid
        return request("UpdateDomainRecord", params)
