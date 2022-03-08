import asyncio
from bleak import BleakScanner, BleakClient


CHARACTERISTIC_UUID_TX = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
CHARACTERISTIC_UUID_RX = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'


async def discover(dev):
    #print(dev.metadata)
    client = BleakClient(dev)
    res = None
    try:
        #print('connecting')
        await client.connect()
        #print('connected')
        #def callback(sender: int, data: bytearray):
        #    nonlocal res
        #    #print(f'{sender}: {data}')
        #    res = data
        #await client.start_notify(CHARACTERISTIC_UUID_RX, callback)
        await client.write_gatt_char(CHARACTERISTIC_UUID_TX, bytes([0]))
        res = await client.read_gatt_char(CHARACTERISTIC_UUID_RX)
        #await asyncio.sleep(0.5)
    except Exception as e:
        #print(e)
        ...
    finally:
        if (res == None): await client.disconnect()
        return (res, client)

async def main():
    devices = await BleakScanner.discover(timeout=2)
    tasks = []
    for d in devices:
        print(d)
        tasks.append(discover(d))

    for t in tasks:
        print(await t)

asyncio.run(main())