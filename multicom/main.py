from typing import List, Set, Tuple

import asyncio


class Device():
    """
    Base class for generated device objects
    """

    def __init__(self, discovery_msg: str):
        self.discovery_msg = discovery_msg


class Channel():
    """
    Base class for various communication implementations
    """

    def __init__(self):

        # dict with devices
        self.devices = { }

    async def start_discovery(self): pass


class Client():
    """
    multicom client wrapper for various backends/channels
    """

    def __init__(self):
        self.channels = []

    def add_channel(self, channel: Channel):
        self.channels.append(channel)
    
    def send_discover(self) -> Tuple[asyncio.AbstractEventLoop, List[asyncio.Task]]:
        loop = asyncio.get_event_loop()
        tasks = []
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

