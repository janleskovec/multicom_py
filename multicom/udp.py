from typing import List
from typing import Callable

import socket
import asyncio
import threading
import ipaddress

from multicom.packet import PacketType

from .main import *


class UdpDevice(Device):
    """
    Udp device implementation
    """

    def __init__(self, channel, dev_data: DiscoveryData, addr: str, port: int):
        super().__init__(dev_data)
        self.channel = channel # to access the socket
        self.addr = addr
        self.port = port
    
    def send(self, data):
        self.channel.sock.sendto(bytes(data), (self.addr, self.port))


class UdpChannel(Channel):
    """
    Udp comm implementation
    """

    def __init__(self, target_port=5021, local_ip='', subnet=None):
        super().__init__()
        self.target_port = target_port
        self.local_ip = local_ip
        self.subnet = subnet
        if self.subnet == None:
            self.broadcast = '<broadcast>'
        else:
            self.subnet = ipaddress.IPv4Network(self.subnet)
            self.broadcast = str(self.subnet.broadcast_address)

        # open socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((self.local_ip, 0))
        # start thread
        self._recv = threading.Thread(target=self._recv)
        self._recv.daemon = True
        self._recv.start()
    
    def _recv(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(2560)
                self.client._on_msg(self, data, addr)
            except socket.timeout:
                break

    async def start_discovery(self):

        MESSAGE = bytes([0x00])

        # send msg 5x
        for _ in range(5):
            self.sock.sendto(MESSAGE, (self.broadcast, self.target_port))
            await asyncio.sleep(0.2)
    
    def add_update_device(self, dev_data: DiscoveryData, extra_data):
        addr, port = extra_data
        # dev_id is used as the key
        # if dev object should be persistent, check first
        self.devices[dev_data.dev_id] = UdpDevice(self, dev_data, addr, port)
