#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import socket

def _convert_port(s_port: str, default: int) -> int:
    if not s_port:
        return default
    try:
        i_port = int(s_port)
    except ValueError as e:
        raise ValueError(
            "端口不是数字"
        ) from e
    if i_port >= 0 and i_port <= 65535:
        return i_port
    else:
        raise ValueError(
            "端口应该在0-65535之间"
        )

def _convert_ip(ip: str, default: str) -> str:
    if not ip:
        return default
    try:
        return socket.inet_ntoa(socket.inet_aton(ip))
    except OSError as e:
        raise ValueError(
            "IP格式错误"
        ) from e

def convert_addr(addr, default_ip):
    # type: (str | None, str) -> socket._RetAddress | None
    if addr is None:
        return None
    addr = addr.strip()
    if not addr:
        return None
    tmp = addr.split(":")
    if len(tmp) == 2:
        return (_convert_ip(tmp[0], default_ip), _convert_port(tmp[1], 25565))
    else:
        raise ValueError(
            "地址格式错误，仅能有一个分隔符"
        )

def convert_mc_host(addr):
    # type: (str | None) -> socket._RetAddress
    if addr is None:
        return ("", 0)
    addr = addr.strip()
    if not addr:
        return ("", 0)
    if addr[0] == "[":
        tmp = addr[1:].split("]")
        if len(tmp) == 2:
            if not tmp[1]:
                tmp[1] = ":"
            if tmp[1][0] != ":":
                raise ValueError(
                    "地址格式错误，无分隔符"
                )
            if not tmp[0]:
                return ("", _convert_port(tmp[1][1:], 0))
            return (tmp[0], _convert_port(tmp[1][1:], 0))
        else:
            raise ValueError(
                "IPv6地址格式错误"
            )
    else:
        tmp = addr.split(":")
        if len(tmp) == 2:
            if not tmp[0]:
                return ("", _convert_port(tmp[1], 0))
            return (tmp[0], _convert_port(tmp[1], 0))
        elif len(tmp) == 1:
            return (tmp[0], 0)
        else:
            raise ValueError(
                "地址格式错误，过多分隔符"
            )
