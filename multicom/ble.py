import socket
import asyncio
from bleak import BleakScanner, BleakClient

from .main import *

SERVICE_UUID           = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
CHARACTERISTIC_UUID_TX = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
CHARACTERISTIC_UUID_RX = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'


class BleDevice(Device):
    """
    BLE device implementation
    """

    def __init__(self, channel, dev_data: DiscoveryData, client: BleakClient):
        super().__init__(dev_data)
        self.channel = channel # to access the channel
        self.client = client
    
    async def _connect(self):
        if not self.client.is_connected:
            await self.client.connect()

        if len(self.client._notification_callbacks) == 0:
            def callback(sender: int, data: bytearray):
                nonlocal self
                self.channel.client._on_msg(self.channel, bytes(data), self.client)

            await self.client.start_notify(CHARACTERISTIC_UUID_RX, callback)
    
    async def send(self, data):
        await self._connect()
        await self.client.write_gatt_char(CHARACTERISTIC_UUID_TX, bytes(data))


class BleChannel(Channel):
    """
    BLE comm implementation
    """

    def __init__(self):
        super().__init__()
    
    async def discover(self, dev):
        MESSAGE = bytes([0x00])

        res = None
        client = BleakClient(dev)
        try:
            await client.connect()
            await client.write_gatt_char(CHARACTERISTIC_UUID_TX, MESSAGE)
            res = await client.read_gatt_char(CHARACTERISTIC_UUID_RX)
            if res != None and len(res) > 0:
                pckt_type = self.client._on_msg(self, res, client)
                if pckt_type != PacketType.DISCOVERY_HELO:
                    await client.disconnect()
        except Exception as e:
            #print(e)
            ...
        finally:
            if (res == None): await client.disconnect()

    async def start_discovery(self):

        devices = await BleakScanner.discover(timeout=2)
        tasks = []
        for d in devices:
            #print(d)
            tasks.append(self.discover(d))

        for t in tasks:
            await t
    
    def add_update_device(self, dev_data: DiscoveryData, extra_data):
        client: BleakClient = extra_data

        # dev_id is used as the key
        if dev_data.dev_id not in self.devices:
            self.devices[dev_data.dev_id] = BleDevice(self, dev_data, client)
