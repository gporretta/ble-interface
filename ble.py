import asyncio
from bleak import BleakClient
from datetime import datetime

#Written by Gino Porretta, gmp7878@g.rit.edu

HM10_ADDRESS = "68:5E:1C:26:D5:D3"  # CHANGE THIS TO HM10_ADDRESS FOUND USING THE SCANNER
CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Standard HM-10 read/write UUID

# Global variables
log_file = None
receive_buffer = ""  # Buffer to accumulate partial messages

# Callback function for receiving data from HM-10
def read_callback(sender, data):
    global receive_buffer, log_file
    decoded = data.decode('utf-8')
    receive_buffer += decoded

    # Process complete lines
    while '\n' in receive_buffer:
        line, receive_buffer = receive_buffer.split('\n', 1)
        print(line, flush=True)
        if log_file:
            log_file.write(line + '\n')
            log_file.flush()

# Send input over BLE to HM-10
async def user_input_writer(client, char_uuid):
    while True:
        message = await asyncio.get_event_loop().run_in_executor(None, input, "Enter message (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        message_with_newline = message + '\n'
        await client.write_gatt_char(char_uuid, message_with_newline.encode('utf-8'))
        print(f"Sent: {message}")

# Main connection and communication loop
async def connect_and_communicate(address, char_uuid):
    global log_file
    async with BleakClient(address) as client:
        if not client.is_connected:
            print("Failed to connect.")
            return

        print("Connected to HM-10")

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"HM10_log_{timestamp}.txt"
        log_file = open(filename, "a")
        print(f"Logging to {filename}")

        # Subscribe to notifications
        await client.start_notify(char_uuid, read_callback)

        # Run user input in parallel with notifications
        await user_input_writer(client, char_uuid)

        # Stop notifications and close file
        await client.stop_notify(char_uuid)
        log_file.close()
        log_file = None
        print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(connect_and_communicate(HM10_ADDRESS, CHARACTERISTIC_UUID))
