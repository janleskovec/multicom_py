import asyncio
from bleak import BleakClient

CHARACTERISTIC_UUID_TX = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
CHARACTERISTIC_UUID_RX = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'

async def main():
    client = BleakClient('50:02:91:8E:E0:6A')
    try:
        print('connecting')
        await client.connect()
        print('connected')
        def callback(sender: int, data: bytearray):
            print(f'{sender}: {data}')
        await client.start_notify(CHARACTERISTIC_UUID_RX, callback)

        await client.write_gatt_char(CHARACTERISTIC_UUID_TX, bytes([0]))

        await asyncio.sleep(1)
    except Exception as e:
        print(e)
    finally:
        await client.disconnect()

asyncio.run(main())