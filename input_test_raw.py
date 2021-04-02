import asyncio
import time
import joystick


DEBUG = False


def button_update(button, val):
    print("Button: ", button, val)


def stick_update(button, val):
    print("Stick:  ", button, val)


def normalize(value):
    return max(min(value, 32767), -32767) / 32767


async def main():
    # Pro Controller Keymap
    buttons = {
        0: 'b',
        1: 'a',
        2: 'x',
        3: 'y',
        4: 'l',
        5: 'r',
        6: 'zl',
        7: 'zr',
        8: 'minus',
        9: 'plus',
        10: 'home',
        11: 'l_stick',
        12: 'r_stick',
        13: 'up',
        14: 'down',
        15: 'left',
        16: 'right',
    }
    analogs = {
        0: {"name": 'l_stick_analog', "direction": 'h'},
        1: {"name": 'l_stick_analog', "direction": 'v'},
        2: {"name": 'r_stick_analog', "direction": 'h'},
        3: {"name": 'r_stick_analog', "direction": 'v'}
    }

    last_axis = [ 2047, 2047, 2047, 2047 ]
    async for event in joystick.joystick_poll(0):
        _timestamp, value, type, number = event
        if type == joystick.EVENT_BUTTON:
            button_update(buttons[number], value)
        elif type == joystick.EVENT_AXIS:
            what = analogs[number]
            axis = normalize(value)
            if what["direction"] == "h":
                last_axis[number] = min(max(int((axis + 1) / 2 * 4095), 0), 4095)
            else:
                last_axis[number] = min(max(int((-axis + 1) / 2 * 4095), 0), 4095)
            base = number - (number & 1)
            print(base)
            print(base + 1)
            stick_update(what["name"], {"h": last_axis[base], "v": last_axis[base + 1]})



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Control-C detected. Bye")
        exit(0)
