#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import struct, socket

# PROXY Protocol v2 Specification:
# https://www.haproxy.org/download/2.9/doc/proxy-protocol.txt

# --- PROXY Protocol v1 ---

def build_pp_v1_header(src_addr: tuple, dst_addr: tuple) -> bytes:
    src_ip, src_port = src_addr[0], src_addr[1]
    dst_ip, dst_port = dst_addr[0], dst_addr[1]

    try:
        socket.inet_pton(socket.AF_INET6, src_ip)
        proto = "TCP6"
    except (socket.error, OSError):
        proto = "TCP4"

    header = f"PROXY {proto} {src_ip} {dst_ip} {src_port} {dst_port}\r\n"
    return header.encode("ascii")


# --- PROXY Protocol v2 ---

PP2_SIGNATURE = b"\x0d\x0a\x0d\x0a\x00\x0d\x0a\x51\x55\x49\x54\x0a"

PP2_VERSION = 0x20
PP2_CMD_PROXY = 0x01  # PROXY command

PP2_AF_INET  = 0x10  # IPv4
PP2_AF_INET6 = 0x20  # IPv6

PP2_PROTO_STREAM = 0x01  # TCP


def build_pp_v2_header(src_addr: tuple, dst_addr: tuple) -> bytes:
    src_ip, src_port = src_addr[0], src_addr[1]
    dst_ip, dst_port = dst_addr[0], dst_addr[1]
    try:
        src_packed = socket.inet_pton(socket.AF_INET, src_ip)
        dst_packed = socket.inet_pton(socket.AF_INET, dst_ip)
        family = PP2_AF_INET
        addr_data = src_packed + dst_packed + struct.pack("!HH", src_port, dst_port)
    except (socket.error, OSError):
        src_packed = socket.inet_pton(socket.AF_INET6, src_ip)
        dst_packed = socket.inet_pton(socket.AF_INET6, dst_ip)
        family = PP2_AF_INET6
        addr_data = src_packed + dst_packed + struct.pack("!HH", src_port, dst_port)

    ver_cmd = PP2_VERSION | PP2_CMD_PROXY
    fam_proto = family | PP2_PROTO_STREAM
    addr_len = len(addr_data)

    header = PP2_SIGNATURE + struct.pack("!BBH", ver_cmd, fam_proto, addr_len) + addr_data
    return header
