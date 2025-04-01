import asyncio
from bleak import BleakClient
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import time
import os
import threading

# Written by Gino Porretta, gmp7878@g.rit.edu

# BLE configuration
HM10_ADDRESS = "68:5E:1C:26:D5:D3"
CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Logging & streaming
log_file = None
receive_buffer = ""
log_filename = None
running = True

# ------------------------ BLE CALLBACK ------------------------

def read_callback(sender, data):
    global receive_buffer, log_file
    decoded = data.decode('utf-8')
    receive_buffer += decoded

    while '\n' in receive_buffer:
        line, receive_buffer = receive_buffer.split('\n', 1)
        if log_file:
            log_file.write(line + '\n')
            log_file.flush()

# ------------------------ BLE CONNECTION ------------------------

async def user_input_writer(client, char_uuid):
    while running:
        message = await asyncio.get_event_loop().run_in_executor(None, input, "Enter message (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        message_with_newline = message + '\n'
        await client.write_gatt_char(char_uuid, message_with_newline.encode('utf-8'))
        print(f"Sent: {message}")

async def connect_and_stream(address, char_uuid):
    global log_file, log_filename
    async with BleakClient(address) as client:
        if not client.is_connected:
            print("Failed to connect.")
            return

        print("Connected to HM-10")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"HM10_log_{timestamp}.txt"
        log_file = open(log_filename, "a")
        print(f"Logging to {log_filename}")

        await client.start_notify(char_uuid, read_callback)
        await user_input_writer(client, char_uuid)
        await client.stop_notify(char_uuid)

        log_file.close()
        log_file = None
        print("Disconnected.")

# ------------------------ DASHBOARD ------------------------

def parse_log(filename):
    try:
        with open(filename, "r", encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]

        records = []
        i = 0
        while i < len(lines) - 4:
            try:
                if lines[i].startswith("Avg Brightness"):
                    brightness = float(lines[i].split(":")[1].strip())
                    com = float(lines[i+1].split(":")[1].strip())
                    angle = float(lines[i+2].split(":")[1].strip())
                    speed = float(lines[i+3].split(":")[1].strip())
                    camera_line = lines[i+4]
                    if camera_line.startswith("Camera Data:"):
                        camera_data = list(map(int, camera_line.split(":", 1)[1].strip().split()))
                        records.append({
                            "Avg Brightness": brightness,
                            "COM": com,
                            "Servo Angle": angle,
                            "Motor Speed": speed,
                            "Camera Data": camera_data
                        })
                        i += 5
                    else:
                        i += 1
                else:
                    i += 1
            except Exception as e:
                print(f"Skipping bad data at line {i}: {e}")
                i += 1
        return records
    except:
        return []

def run_dashboard():
    global log_filename, running
    plt.ion()
    fig, axs = plt.subplots(2, 2, figsize=(12, 6))
    line_scan_fig, line_scan_ax = plt.subplots(figsize=(10, 4))

    print("Starting live dashboard...")
    while running:
        if not log_filename or not os.path.exists(log_filename):
            time.sleep(1)
            continue

        records = parse_log(log_filename)
        if not records:
            time.sleep(1)
            continue

        df = pd.DataFrame(records)

        axs[0, 0].cla(); axs[0, 0].plot(df["Avg Brightness"]); axs[0, 0].set_title("Avg Brightness")
        axs[0, 1].cla(); axs[0, 1].plot(df["COM"]); axs[0, 1].set_title("COM")
        axs[1, 0].cla(); axs[1, 0].plot(df["Servo Angle"]); axs[1, 0].set_title("Servo Angle")
        axs[1, 1].cla(); axs[1, 1].plot(df["Motor Speed"]); axs[1, 1].set_title("Motor Speed")

        for ax in axs.flat:
            if ax.get_visible():
                ax.set_xlabel("Sample #")
        fig.tight_layout()
        fig.canvas.draw(); fig.canvas.flush_events()

        line_scan_ax.cla()
        line_scan_ax.plot(df.iloc[-1]["Camera Data"])
        line_scan_ax.set_title("Most Recent Camera Data")
        line_scan_ax.set_xlabel("Pixel")
        line_scan_ax.set_ylabel("Brightness")
        line_scan_fig.canvas.draw(); line_scan_fig.canvas.flush_events()

        time.sleep(1)

# ------------------------ MAIN ------------------------

if __name__ == "__main__":
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()

    asyncio.run(connect_and_stream(HM10_ADDRESS, CHARACTERISTIC_UUID))