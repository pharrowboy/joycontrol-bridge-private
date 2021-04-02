import asyncio

import time
import struct

import joystick


DEBUG = False


def button_update(button, val):
    print("Button: ", button, val)


def stick_update(button, val):
    print("Stick:  ", button, val)


async def main():
    buttons = {
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
    }
    analogs = {
        'l_stick_analog': [0, 1],
        'r_stick_analog': [2, 3]
    }
    buttons = dict((val, key) for key, val in buttons.items())
    list_buttons = list(buttons.keys())
    list_analogs = list(analogs.keys())
    async for event in joystick.joystick_poll(0):
        print("Time: {} | Value: {} | Type: {} | Number: {}".format(
              event.timestamp, event.value, event.kind, event.number))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Control-C detected. Bye")
        exit(0)
