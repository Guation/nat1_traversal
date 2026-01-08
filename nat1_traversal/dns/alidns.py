#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["update_record", "init"]

import time, uuid, hashlib, hmac, requests, json
from urllib.parse import quote, urlencode
from logging import debug, info, warning, error
from .util import USER_AGENT, domain2punycode

__id: str = None
__token: str = None

def init(id: str, token: str):
    global __id, __token
    __id = id
    __token = token

def flattening_params(params, prefix = "", upper_params: dict = None):
    if upper_params is None:
        upper_params = {}
    if params is None:
        return upper_params
    elif isinstance(params, (list, tuple)):
        for i, item in enumerate(params):
            flattening_params(item, f"{prefix}.{i + 1}", upper_params)
    elif isinstance(params, dict):
        for sub_key, sub_value in params.items():
            flattening_params(sub_value, f"{prefix}.{sub_key}", upper_params)
    else:
        prefix = prefix.lstrip(".")
        upper_params[prefix] = params.decode("utf-8") if isinstance(params, bytes) else str(params)
    return upper_params

def request(action: str, params: dict = None):
    headers = {
        "host": "alidns.aliyuncs.com",
        "x-acs-action": action,
        "x-acs-version": "2015-01-09",
        "x-acs-date": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "x-acs-signature-nonce": str(uuid.uuid4()),
        "x-acs-content-sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
    headers = dict(sorted(headers.items()))
    canonical_query_string = "&".join(
        f"{quote(k)}={quote(str(v))}"
        for k, v in sorted(flattening_params(params).items())
    )
    canonical_headers = "\n".join(f"{k}:{v}" for k, v in headers.items()) + "\n"
    signed_headers = ";".join(headers.keys())
    canonical_request = "\n".join(["POST", "/", canonical_query_string, canonical_headers, signed_headers, headers["x-acs-content-sha256"]])
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    signature = hmac.new(__token.encode("utf-8"), f"ACS3-HMAC-SHA256\n{hashed_canonical_request}".encode("utf-8"), hashlib.sha256).digest().hex().lower()
    headers["Authorization"] = f"ACS3-HMAC-SHA256 Credential={__id},SignedHeaders={signed_headers},Signature={signature}"
    headers["User-Agent"] = USER_AGENT
    debug("action=%s, params=%s, headers=%s", action, params, headers)
    try:
        response = requests.request("POST", f"https://{headers['host']}/?{urlencode(params, doseq=True, safe='*')}", headers=headers)
        r = response.content
        if response.status_code != 200:
            raise ValueError(
                '服务器拒绝了请求：action=%s, status_code=%d, response=%s' % (action, response.status_code, r)
            )
        else:
            j = json.loads(r)
            debug("action=%s, response=%s", action, j)
            return j
    except ValueError:
        raise
    except Exception as e:
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
