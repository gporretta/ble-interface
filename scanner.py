import asyncio
from bleak import BleakScanner

#Written by Gino Porretta, gmp7878@g.rit.edu

# HM10 Module will either be named DSD TECH by default or CAR# use that
# ID in dashboard.py ensure no trailing : at the end of the ID

async def scan_devices():
    devices = await BleakScanner.discover()
    for device in devices:
        print(device)

if __name__ == "__main__":
    asyncio.run(scan_devices())