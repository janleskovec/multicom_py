#import multicom

from multicom import Client
from multicom import UdpChannel

import asyncio

async def main():
    client = Client()
    client.add_channel(UdpChannel(subnet='192.168.1.0/24'))

    devices = await client.discover_wait()
    print('devices:', list(devices))
    if len(devices) == 0: return

    device_id = list(devices)[0]

    with client.open(device_id) as session:
        for i in range(10):
            session.send('setval', str(i))

if __name__  == '__main__': asyncio.run(main())
