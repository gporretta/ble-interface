import asyncio
from bleak import BleakClient
import re

# Written by Gino Porretta, gmp7878@g.rit.edu

HM10_ADDRESS = "68:5E:1C:26:D5:D3"  # CHANGE THIS TO YOUR HM-10 ADDRESS
CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Standard HM-10 read/write UUID

# Global buffer to accumulate partial messages
receive_buffer = ""

# Callback function for receiving data from HM-10
def read_callback(sender, data):
    global receive_buffer
    decoded = data.decode('utf-8', errors='ignore')
    receive_buffer += decoded

    # Split into lines using common line endings
    lines = re.split(r'\r\n|\r|\n', receive_buffer)
    receive_buffer = lines.pop()  # Keep the last partial line

    for line in lines:
        if line:
            print(line, flush=True)

# Send user input over BLE to HM-10
async def user_input_writer(client, char_uuid):
    print("Enter message (or 'exit' to quit):\n")
    while True:
        message = await asyncio.get_event_loop().run_in_executor(None, input)
        if message.lower() == 'exit':
            break
        message_with_newline = message + '\n'
        await client.write_gatt_char(char_uuid, message_with_newline.encode('utf-8'))
        #print(f"Sent: {message}")

# Main BLE connection and communication loop
async def connect_and_communicate(address, char_uuid):
    async with BleakClient(address) as client:
        if not client.is_connected:
            print("Failed to connect.")
            return

        print("Connected to HM-10")

        # Start receiving notifications
        await client.start_notify(char_uuid, read_callback)
        print("Notifications started.")

        # Handle user input while receiving data
        await user_input_writer(client, char_uuid)

        # Stop receiving notifications
        await client.stop_notify(char_uuid)
        print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(connect_and_communicate(HM10_ADDRESS, CHARACTERISTIC_UUID))
