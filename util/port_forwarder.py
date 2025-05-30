#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import asyncio
from logging import debug, info, warning, error, exception

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
        exception(f"Forwarding error")
    finally:
        writer.close()

async def handle_client(local_reader: asyncio.StreamReader, local_writer: asyncio.StreamWriter, remote_host: str, remote_port: int):
    try:
        client_address = local_writer.get_extra_info('peername')
        info(f"client {client_address[0]}:{client_address[1]} try connect to {remote_host}:{remote_port}")
        remote_reader, remote_writer = await asyncio.open_connection(remote_host, remote_port)
        local_address = remote_writer.get_extra_info('sockname')
        info(f"client {client_address[0]}:{client_address[1]} bind to {local_address[0]}:{local_address[1]}")

        local_to_remote = asyncio.create_task(forward(local_reader, remote_writer))
        remote_to_local = asyncio.create_task(forward(remote_reader, local_writer))

        await asyncio.gather(local_to_remote, remote_to_local)
        info(f"client {client_address[0]}:{client_address[1]} disconnected")
    except Exception:
        exception(f"Connection error")
    finally:
        local_writer.close()

async def handle_client_pong(local_reader: asyncio.StreamReader, local_writer: asyncio.StreamWriter, remote_host: str, remote_port: int):
    global g_handle_client
    g_handle_client = handle_client
    info("pong thread start")
    try:
        while True:
            data = await local_reader.read(4096)
            if not data:
                break
            local_writer.write(b"pong")
            await local_writer.drain()
    except asyncio.CancelledError:
        pass
    except Exception:
        exception(f"Forwarding error")
        exit(1)
    finally:
        local_writer.close()

async def client_ping(internet_ip: str, internet_port: int):
    info("ping thread start")
    reader, writer = None, None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(internet_ip, internet_port), timeout=5)
        while True:
            writer.write(b"ping")
            await writer.drain()
            await reader.read(9999)
            await asyncio.sleep(1)
    except Exception as e:
        error(f"client_ping error: {e}")
        exit(1)
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()

async def port_forward(local_host: str, local_port: int, remote_host: str, remote_port: int, call_host: str, call_port: int):
    global g_handle_client
    g_handle_client = handle_client_pong
    server = await asyncio.start_server(
        lambda r, w: g_handle_client(r, w, remote_host, remote_port),
        local_host,
        local_port
    )
    asyncio.create_task(client_ping(call_host, call_port))
    async with server:
        info(f"Port forwarding from {local_host}:{local_port}({call_host}:{call_port}) to {remote_host}:{remote_port}")
        await server.serve_forever()

def start_port_forward(local_host: str, local_port: int, remote_host: str, remote_port: int, call_host: str, call_port: int):
    asyncio.run(port_forward(local_host, local_port, remote_host, remote_port, call_host, call_port))
