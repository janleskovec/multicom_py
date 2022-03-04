#import multicom

from multicom import Client
from multicom import UdpChannel

import asyncio
import time

async def main():
    client = Client()
    client.add_channel(UdpChannel(subnet='192.168.1.0/24'))

    devices = await client.discover_wait()
    print('devices:', list(devices))
    if len(devices) == 0: return

    device_id = list(devices)[0]

    with client.open(device_id) as session:
        lost = 0
        ms_sum = 0
        start_time = time.time_ns()
        for i in range(1000):
            ping_time = await session.ping()
            if ping_time != None:
                ms_sum += ping_time
                #print(f'{ping_time:.02f}ms')
            else:
                #print('ping timeout')
                lost += 1
        num = i+1
        total_time_s = (time.time_ns() - start_time) / (10**9)
        print(f'num: {num}, lost: {(lost/num):.2f}%, avg time: {(ms_sum/(num-lost)):.2f}ms, pckt/s: {(num/total_time_s):.2f}')

if __name__  == '__main__': asyncio.run(main())
