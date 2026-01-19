#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"
__all__ = ["alicloud_common"]

import time, uuid, hashlib, hmac, requests, json
from nat1_traversal.dns.dns_base import dns_base
from urllib.parse import quote_plus, urlencode
from logging import debug, info, warning, error

class alicloud_common(dns_base):
    def flattening_params(self, params, prefix = "", upper_params: dict = None):
        if upper_params is None:
            upper_params = {}
        if params is None:
            return upper_params
        elif isinstance(params, (list, tuple)):
            for i, item in enumerate(params):
                self.flattening_params(item, f"{prefix}.{i + 1}", upper_params)
        elif isinstance(params, dict):
            for sub_key, sub_value in params.items():
                self.flattening_params(sub_value, f"{prefix}.{sub_key}", upper_params)
        else:
            prefix = prefix.lstrip(".")
            upper_params[prefix] = params.decode("utf-8") if isinstance(params, bytes) else str(params)
        return upper_params

    def alicloud_rpc_request(self, method: str, endpoint: str, action: str, version: str, params: dict):
        headers = {
            "host": endpoint,
            "x-acs-action": action,
            "x-acs-version": version,
            "x-acs-date": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "x-acs-signature-nonce": str(uuid.uuid4()),
            "x-acs-content-sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
        headers = dict(sorted(headers.items()))
        canonical_query_string = "&".join(
            f"{quote_plus(k)}={quote_plus(str(v))}"
            for k, v in sorted(self.flattening_params(params).items())
        )
        canonical_headers = "\n".join(f"{k}:{v}" for k, v in headers.items()) + "\n"
        signed_headers = ";".join(headers.keys())
        canonical_request = "\n".join([method, "/", canonical_query_string, canonical_headers, signed_headers, headers["x-acs-content-sha256"]])
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        signature = hmac.new(self.token.encode("utf-8"), f"ACS3-HMAC-SHA256\n{hashed_canonical_request}".encode("utf-8"), hashlib.sha256).digest().hex().lower()
        headers["Authorization"] = f"ACS3-HMAC-SHA256 Credential={self.id},SignedHeaders={signed_headers},Signature={signature}"
        headers["User-Agent"] = self.USER_AGENT
        debug("action=%s, params=%s, headers=%s", action, params, headers)
        try:
            response = requests.request(method, f"https://{headers['host']}/?{urlencode(params, doseq=True, safe='*')}", headers=headers)
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
