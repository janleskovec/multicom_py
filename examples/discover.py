#import multicom

from multicom import Client
from multicom import UdpChannel

def main():
    client = Client()
    client.add_channel(UdpChannel(subnet='192.168.1.0/24'))

    print('devices:', client.discover_wait())

if __name__  == '__main__': main()
