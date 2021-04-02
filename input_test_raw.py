import asyncio
import aiofiles
import time
import struct


DEBUG = False

# u32 time, s16 val, u8 type, u8 num
EVENT_FORMAT = "LhBB"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)


def button_update(button, val):
    print("Button: ", button, val)


def stick_update(button, val):
    print("Stick:  ", button, val)


async def main():
    buttons = [
        'b':       0,
        'a':       1,
        'x':       2,
        'y':       3,
        'l':       4,
        'r':       5,
        'zl':      6,
        'zr':      7,
        'minus':   8,
        'plus':    9,
        'home':    10,
        'l_stick': 11,
        'r_stick': 12,
        'up':      13,
        'down':    14,
        'left':    15,
        'right':   16,
    ]
    analogs = {
        'l_stick_analog': [0, 1],
        'r_stick_analog': [2, 3]
    }
    buttons = dict((val, key) for key, val in buttons.items())
    list_buttons = list(buttons.keys())
    list_analogs = list(analogs.keys())
    async with aiofiles.open("/dev/input/js0", "rb") as joystick:
        while True:
            event = await joystick.read(EVENT_SIZE)
            if not event:
                break
            event_time, event_value, event_type, event_number = struct.unpack(
                EVENT_FORMAT, event)
            print("Time: {} | Value: {} | Type: {} | Number: {}",
                  event_time, event_value, event_type, event_number)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Control-C detected. Bye")
        pass
