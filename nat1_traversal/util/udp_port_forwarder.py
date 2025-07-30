#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import selectors, traceback, os, sys, time, socket
from logging import debug, info, warning, error, exception
from .stun import new_udp_socket, MTU
from typing import Callable

def stop():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)

class server_handle:
    def __init__(self, local, remote, call) -> None:
        # type: (socket._Address, socket._Address, socket._Address) -> None
        self.remote = remote
        server_socket = new_udp_socket()
        server_socket.bind(local)
        server_socket.setblocking(False)
        self.sock = server_socket
        self.sel = selectors.DefaultSelector()
        self.sel.register(server_socket, selectors.EVENT_READ, self.handle)
        self.client_maps = dict()
        self.create_client = self.create_client2
        self.pong = pong_handle()
        self.sel.register(self.pong.sock, selectors.EVENT_READ, self.pong.handle)
        self.ping = ping_handle(call)
        self.sel.register(self.ping.sock, selectors.EVENT_READ, self.ping.handle)

    def create_client1(self, source):
        # type: (socket._Address) -> client_handle
        client_socket = new_udp_socket()
        client_socket.setblocking(False)
        client_socket.connect(self.remote)
        ch = client_handle(client_socket, source, self.sock.sendto)
        self.sel.register(client_socket, selectors.EVENT_READ, ch.handle)
        info(f"新客户端 {source[0]}:{source[1]} ，绑定到本地地址 {client_socket.getsockname()[0]}:{client_socket.getsockname()[1]}")
        return ch

    def create_client2(self, source): # 第一个连接重定向到ping-pong
        # type: (socket._Address) -> client_handle
        self.create_client = self.create_client1
        client_socket = new_udp_socket()
        client_socket.setblocking(False)
        client_socket.connect(self.pong.sock.getsockname())
        ch = client_handle(client_socket, source, self.sock.sendto)
        self.sel.register(client_socket, selectors.EVENT_READ, ch.handle)
        return ch

    def clear_client(self):
        target_time = time.perf_counter() - 30
        need_del = []
        for k, v in self.client_maps.items():
            if v.lifetime < target_time:
                need_del.append(k)
                self.sel.unregister(v.sock)
                v.sock.close()
                info(f"客户端 {k[0]}:{k[1]} 停止活动，断开连接")
        for i in need_del:
            del self.client_maps[i]

    def handle(self):
        data, source = self.sock.recvfrom(MTU)
        client = self.client_maps.get(source)
        if client is None:
            client = self.create_client(source)
            self.client_maps[source] = client
        client.lifetime = time.perf_counter()
        client.sock.send(data)

    def start(self):
        clean_time = time.perf_counter() + 30
        ping_time = time.perf_counter() + 1
        self.ping.first_send()
        while True:
            events = self.sel.select(timeout=0.1)
            for key, mask in events:
                key.data()
            now_time = time.perf_counter()
            if clean_time <= now_time:
                clean_time = now_time + 30
                self.clear_client()
            if ping_time <= now_time:
                ping_time = now_time + 1
                self.ping.send()

class client_handle:
    def __init__(self, sock, source, send_func):
        # type: (socket.socket, socket._Address, Callable[[bytes, socket._Address], None]) -> None
        self.sock = sock
        self.source = source
        self.send_func = send_func
        self.lifetime = time.perf_counter()

    def handle(self):
        try:
            self.send_func(self.sock.recv(MTU), self.source)
        except OSError:
            warning(f"转发错误，客户端 {self.source[0]}:{self.source[1]} 无法连接到 {self.sock.getpeername()[0]}:{self.sock.getpeername()[1]}")
            debug(traceback.format_exc())

class ping_handle:
    def __init__(self, remote):
        # type: (socket._Address) -> None
        client_socket = new_udp_socket()
        client_socket.setblocking(False)
        client_socket.connect(remote)
        self.sock = client_socket
        self.lost = 0
        info("开始ping线程")

    def first_send(self):
        for _ in range(3):
            self.sock.send(b"ping")

    def send(self):
        self.lost += 1
        if self.lost >= 5:
            error(f"ping线程异常，无法收到pong线程响应")
            stop()
        self.sock.send(b"ping")

    def handle(self):
        if self.sock.recv(MTU) == b"pong":
            self.lost = 0

class pong_handle:
    def __init__(self):
        # type: () -> None
        server_socket = new_udp_socket()
        server_socket.bind(("127.0.0.1", 0))
        server_socket.setblocking(False)
        self.sock = server_socket
        info("开始pong线程")

    def handle(self):
        data, source = self.sock.recvfrom(MTU)
        if data == b"ping":
            self.sock.sendto(b"pong", source)

def start_udp_port_forward(local, remote, call):
    # type: (socket._Address, socket._Address, socket._Address) -> None
    server_handle(local, remote, call).start()
