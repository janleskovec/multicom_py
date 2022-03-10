from http import client
from tracemalloc import start
from typing import List, Set, Tuple

import asyncio
import random
import time

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
    
    async def send(self, data):
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

        self.timeout = 8

        self.nonce = 1 # must start with 1
        self.id = bytes([random.randint(0,255) for _ in range(4)])

        self.request_futures = { }
    
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_value, tb): pass

    def _on_msg(self, data):
        pckt_type = PacketType(data[0])
        # session_id = data[1:5] # unused
        nonce = data[5:9]
        msg = data[9:]

        if nonce in self.request_futures:
            # complete future thread-safely
            future = self.request_futures[nonce]
            loop = future.get_loop()

            if pckt_type == PacketType.PING:
                loop.call_soon_threadsafe(future.set_result, True)
            elif pckt_type == PacketType.NOT_FOUND:
                print('not found') # TODO: exception handling?
                loop.call_soon_threadsafe(future.set_result, None)
            elif pckt_type == PacketType.GET_REPLY:
                msg_strings = msg.decode('ascii').split('\0')
                loop.call_soon_threadsafe(future.set_result, msg_strings[0])
            elif pckt_type == PacketType.ACK:
                loop.call_soon_threadsafe(future.set_result, True)
    
    async def ping(self):
        loop = asyncio.get_running_loop()

        nonce = bytes([random.randint(0,255) for _ in range(4)])

        start_time = time.time_ns()

        on_completed = loop.create_future()
        self.request_futures[nonce] = on_completed

        await self.client.get_device(self.dev_id).send(
            [PacketType.PING.value] +
            list(self.id) +
            list(nonce)
        )

        on_completed = asyncio.wait_for(on_completed, timeout=self.timeout)

        try:
            await on_completed
            return (time.time_ns() - start_time) / (10**6)
        except asyncio.exceptions.TimeoutError:
            print('ping timeout')

        del self.request_futures[nonce]
    
    async def get(self, endpoint: str, data='', num_retransmit=4):
        loop = asyncio.get_running_loop()

        nonce = bytes([random.randint(0,255) for _ in range(4)])

        res = None

        for _ in range(num_retransmit):
            on_completed = loop.create_future()
            self.request_futures[nonce] = on_completed

            await self.client.get_device(self.dev_id).send(
                [PacketType.GET.value] +
                list(self.id) +
                list(nonce) +
                list(endpoint.encode(encoding='ascii')) + [0] +
                list(data.encode(encoding='ascii'))
            )

            on_completed = asyncio.wait_for(on_completed, timeout=self.timeout/num_retransmit)

            try:
                res = await on_completed
            except asyncio.exceptions.TimeoutError:
                print('get timeout')

        del self.request_futures[nonce]

        return res
    
    async def send(self, endpoint: str, data=''):

        nonce = self.nonce.to_bytes(4, byteorder='big', signed=False)
        self.nonce += 1

        await self.client.get_device(self.dev_id).send(
            [PacketType.SEND.value] +
            list(self.id) +
            list(nonce) +
            list(endpoint.encode(encoding='ascii')) + [0] +
            list(data.encode(encoding='ascii'))
        )
    
    async def post(self, endpoint: str, data='', num_retransmit=4):
        loop = asyncio.get_running_loop()

        nonce = self.nonce.to_bytes(4, byteorder='big', signed=False)
        self.nonce += 1

        res = None
        for _ in range(num_retransmit):
            on_completed = loop.create_future()
            self.request_futures[nonce] = on_completed

            await self.client.get_device(self.dev_id).send(
                [PacketType.POST.value] +
                list(self.id) +
                list(nonce) +
                list(endpoint.encode(encoding='ascii')) + [0] +
                list(data.encode(encoding='ascii'))
            )

            on_completed = asyncio.wait_for(on_completed, timeout=self.timeout/num_retransmit)

            try:
                res = await on_completed
            except asyncio.exceptions.TimeoutError:
                print('post timeout')

        del self.request_futures[nonce]

        return res



class Client():
    """
    multicom client wrapper for various backends/channels
    """

    def __init__(self):
        self.channels = []
        self.sessions = {}

    def add_channel(self, channel: Channel):
        # allow
        ## prevent duplicate channel types
        #for c in self.channels:
        #    if type(c) == type(channel): return
        
        # add to list
        self.channels.append(channel)
        channel.client = self

    def _on_msg(self, channel: Channel, data: bytes, extra_data) -> PacketType:
        pckt_type = PacketType(data[0])
        session_id = data[1:5]
        if pckt_type == PacketType.DISCOVERY_HELO:
            ddata = DiscoveryData(data[1:])
            if ddata.dev_id != None:
                channel.add_update_device(ddata, extra_data)
        else:
            if session_id in self.sessions:
                self.sessions[session_id]._on_msg(data)
        
        return pckt_type
            
    
    def send_discover(self) -> Tuple[asyncio.AbstractEventLoop, List[asyncio.Task]]:
        loop = asyncio.get_running_loop()
        tasks = [ ]
        for ch in self.channels:
            tasks.append(loop.create_task(ch.start_discovery()))

        return tasks

    async def discover_wait(self, wait_s=4) -> Set[str]:
        loop = asyncio.get_running_loop()

        tasks = self.send_discover()
        tasks.append(loop.create_task(asyncio.sleep(wait_s)))

        for f in tasks:
            await f
        
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

    def open(self, dev_id: str) -> Session:
        device = self.get_device(dev_id)
        if device != None:
            new_session = Session(self, dev_id)
            self.sessions[new_session.id] = new_session
            return new_session
