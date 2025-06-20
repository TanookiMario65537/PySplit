import socket
import evdev
from evdev import InputDevice, categorize, ecodes

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/keyboard.sock")

devices = [InputDevice(path) for path in evdev.list_devices()]
for i, dev in enumerate(devices):
    print(f"{i}: {dev.path} - {dev.name}")

# Select the keyboard device (adjust index if needed)
keyboard = devices[4]  # or whichever one is your actual keyboard

for event in keyboard.read_loop():
    if event.type == ecodes.EV_KEY:
        key_event = categorize(event)
        msg = f"{key_event.keycode},{key_event.keystate}"
        sock.sendall((msg + "\n").encode())
