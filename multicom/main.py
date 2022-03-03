from http import client
from typing import List, Set, Tuple

import asyncio
import random

from multicom.packet import PacketType


class DiscoveryData():
    """
    Discovery packet data parser
    """

    def __init__(self, discovery_msg: bytes):
        try:
            _decoded = discovery_msg.decode('ascii').split('\0')
            self.fw_id = _decoded[0]
            self.dev_id = _decoded[1]
            self.api_ver = int(_decoded[2])
        # parsing failed
        except Exception:
            self.fw_id = None
            self.dev_id = None
            self.api_ver = None
    
    def __str__(self) -> str:
        return f'(fw_id: "{self.fw_id}", dev_id: "{self.dev_id}", api_ver: "{self.api_ver}")'

class Device():
    """
    Base class for generated device objects
    """

    def __init__(self, dev_data: DiscoveryData):
        self.dev_data = dev_data
    
    def send(self, data):
        raise NotImplementedError("Please Implement this method")


class Channel():
    """
    Base class for various communication implementations
    """

    def __init__(self):

        # dict with devices
        self.devices = { }

    async def start_discovery(self):
        raise NotImplementedError("Please Implement this method")

    def add_update_device(self, dev_data: DiscoveryData, extra_data):
        raise NotImplementedError("Please Implement this method")


class Session():
    """
    Session class (manages nonce counters and message queues)
    """

    def __init__(self, client, dev_id: str):
        self.client = client
        self.dev_id = dev_id

        self.nonce = 1 # must start with 1
        self.id = list([random.randint(0,255) for _ in range(4)])
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb): pass
    
    def ping(self):
        self.client.get_device(self.dev_id).send(
            [PacketType.PING.value[0]] +
            self.id
        )


class Client():
    """
    multicom client wrapper for various backends/channels
    """

    def __init__(self):
        self.channels = []

    def add_channel(self, channel: Channel):
        # prevent duplicate channel types
        for c in self.channels:
            if type(c) == type(channel): return
        
        # add to list
        self.channels.append(channel)
        channel.client = self

    def _on_msg(self, channel: Channel, data: bytes, extra_data):
        if data[0] == PacketType.DISCOVERY_HELO.value[0]:
            ddata = DiscoveryData(data[1:])
            if ddata.dev_id != None:
                channel.add_update_device(ddata, extra_data)
        elif data[0] == PacketType.PING.value[0]:
            msg = data[1:]
            print(f'ping response from: {extra_data}, msg: {msg}')
    
    def send_discover(self) -> Tuple[asyncio.AbstractEventLoop, List[asyncio.Task]]:
        loop = asyncio.get_event_loop()
        tasks = [ ]
        for ch in self.channels:
            tasks.append(loop.create_task(ch.start_discovery()))

        return loop, tasks

    def discover_wait(self, wait_s=4) -> Set[str]:

        loop, tasks = self.send_discover()
        tasks.append(loop.create_task(asyncio.sleep(wait_s)))

        for f in tasks:
            loop.run_until_complete(f)
        
        devices = set()
        for c in self.channels:
            for key in c.devices:
                devices.add(key)

        return devices

    def get_device(self, dev_id: str) -> Device:
        for ch in self.channels:
            if dev_id in ch.devices:
                return ch.devices[dev_id]
    
    def __getitem__(self, key) -> Device:
        return self.get_device(key)

    def open(self, dev_id: str):
        device = self.get_device(dev_id)
        if device != None:
            return Session(self, dev_id)

