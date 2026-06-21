#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import asyncio, traceback, os, sys, socket
from logging import debug, info, warning, error, exception
from .stun import new_tcp_socket

_proxy_protocol_version = None

def set_proxy_protocol_version(version):
    """Set the proxy protocol version for this forwarder process."""
    global _proxy_protocol_version
    _proxy_protocol_version = version

def stop():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)

async def forward(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except asyncio.CancelledError:
        pass
    except Exception:
        error(f"转发错误")
        debug(traceback.format_exc())
    finally:
        writer.close()

async def handle_client(local_reader: asyncio.StreamReader, local_writer: asyncio.StreamWriter, remote_host: str, remote_port: int):
    client_address = local_writer.get_extra_info('peername')
    try:
        info(f"新客户端 {client_address[0]}:{client_address[1]} 尝试连接到 {remote_host}:{remote_port}")
        remote_reader, remote_writer = await asyncio.open_connection(remote_host, remote_port)
        local_address = remote_writer.get_extra_info('sockname')
        info(f"客户端 {client_address[0]}:{client_address[1]} 已连接，绑定到本地地址 {local_address[0]}:{local_address[1]}")

        if _proxy_protocol_version:
            pp_header = _build_proxy_protocol_header(client_address, (remote_host, remote_port))
            if pp_header:
                remote_writer.write(pp_header)
                await remote_writer.drain()
                info(f"已发送 PROXY Protocol {_proxy_protocol_version} 头，客户端真实地址 {client_address[0]}:{client_address[1]}")

        local_to_remote = asyncio.create_task(forward(local_reader, remote_writer))
        remote_to_local = asyncio.create_task(forward(remote_reader, local_writer))

        await asyncio.gather(local_to_remote, remote_to_local)
        info(f"客户端 {client_address[0]}:{client_address[1]} 断开连接")
    except Exception:
        error(f"转发错误，客户端 {client_address[0]}:{client_address[1]} 无法连接到 {remote_host}:{remote_port}")
        debug(traceback.format_exc())
    finally:
        local_writer.close()

def _build_proxy_protocol_header(src_addr, dst_addr):
    """Build proxy protocol header based on configured version."""
    try:
        if _proxy_protocol_version == "v1":
            from .proxy_protocol import build_pp_v1_header
            return build_pp_v1_header(src_addr, dst_addr)
        elif _proxy_protocol_version == "v2":
            from .proxy_protocol import build_pp_v2_header
            return build_pp_v2_header(src_addr, dst_addr)
    except Exception:
        error("构建 PROXY Protocol 头失败")
        debug(traceback.format_exc())
    return None

async def handle_client_pong(local_reader: asyncio.StreamReader, local_writer: asyncio.StreamWriter, remote_host: str, remote_port: int):
    global g_handle_client
    g_handle_client = handle_client
    info("开始pong线程")
    try:
        while True:
            data = await asyncio.wait_for(local_reader.read(4096), timeout=15)
            if not data:
                break
            local_writer.write(b"pong")
            await local_writer.drain()
    except asyncio.CancelledError:
        pass
    except Exception:
        error(f"pong线程异常，可能是ping线程已离线")
        debug(traceback.format_exc())
        stop()
    finally:
        local_writer.close()

async def client_ping(internet_ip: str, internet_port: int):
    info("开始ping线程")
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(internet_ip, internet_port), timeout=3)
        try:
            while True:
                writer.write(b"ping")
                await writer.drain()
                await asyncio.wait_for(reader.read(9999), timeout=3)
                await asyncio.sleep(1)
        finally:
            writer.close()
    except Exception:
        error(f"ping线程异常，无法连接到pong线程")
        debug(traceback.format_exc())
        stop()

async def port_forward(local_host: str, local_port: int, remote_host: str, remote_port: int, call_host: str, call_port: int):
    global g_handle_client
    g_handle_client = handle_client_pong
    sock = new_tcp_socket()
    sock.bind((local_host, local_port))
    sock.listen()
    sock.setblocking(False)
    server = await asyncio.start_server(
        lambda r, w: g_handle_client(r, w, remote_host, remote_port),
        sock = sock
    )
    asyncio.create_task(client_ping(call_host, call_port))
    async with server:
        pp_info = f"（PROXY Protocol {_proxy_protocol_version}）" if _proxy_protocol_version else ""
        info(f"开启从 {local_host}:{local_port}({call_host}:{call_port}) 到 {remote_host}:{remote_port} 的端口转发{pp_info}")
        await server.serve_forever()

def start_tcp_port_forward(local, remote, call, proxy_protocol_version=None):
    # type: (socket._Address, socket._Address, socket._Address, str | None) -> None
    set_proxy_protocol_version(proxy_protocol_version)
    try:
        asyncio.run(port_forward(*local, *remote, *call))
    except (KeyboardInterrupt, SystemExit):
        return
