#!/usr/bin/python3

from multicom import Client
from multicom import UdpChannel
from multicom import BleChannel

import asyncio

async def main():
    client = Client()
    client.add_channel(UdpChannel(subnet='192.168.1.0/24'))
    client.add_channel(UdpChannel(subnet='10.0.1.0/24'))
    client.add_channel(BleChannel())

    devices = await client.discover_wait()
    print('devices:', list(devices))
    if len(devices) == 0: return

    device_id = list(devices)[0]

    with client.open(device_id) as session:
        # get starting value
        response = await session.get('getval')
        print(f'value on device: "{response}"')
        
        # change value
        await session.post('setval', data='2')
        response = await session.get('getval')
        print(f'value on device: "{response}"')

        # change again
        await session.post('setval', data='1')
        response = await session.get('getval')
        print(f'value on device: "{response}"')

if __name__  == '__main__': asyncio.run(main())
