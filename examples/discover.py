#import multicom

from multicom import Client
from multicom import UdpChannel

import time

def main():
    client = Client()
    client.add_channel(UdpChannel(subnet='192.168.1.0/24'))

    devices = client.discover_wait()
    print('devices:', devices)

    client[list(devices)[0]].ping()

    time.sleep(1) # wait for ping response

if __name__  == '__main__': main()
