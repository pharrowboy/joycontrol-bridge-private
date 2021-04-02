import pygame
import asyncio
import time


DEBUG = False


def button_update(button, val):
    print("Button: ", button, val)


def stick_update(button, val):
    print("Stick:  ", button, val)


def describe_joystick(joystick):
    return "'{}' ({} buttons, {} hats, {} balls, and {} axes)".format(
        joystick.get_name(),
        joystick.get_numbuttons(),
        joystick.get_numhats(),
        joystick.get_numballs(),
        joystick.get_numaxes())


async def main():
    await asyncio.sleep(0)
    pygame.init()
    while True:
        try:
            pygame.joystick.init()
            count = pygame.joystick.get_count()
            print(count, "Controllers connected.")
            for id in range(count):
                joy = pygame.joystick.Joystick(id)
                print(f"{id}: {describe_joystick(joy)}")
                joy.quit()
            if count > 0:
                num = int(input("Controller >> ").rstrip())
                if num < 0 or num >= count:
                    print(num, "is out of range!")
                else:
                    joystick = pygame.joystick.Joystick(num)
                    break
        except pygame.error as e:
            pass
        pygame.joystick.quit()
        time.sleep(0.5)
        continue
    joystick.init()
    print("Initialized Joystick", describe_joystick(joystick))

    buttons = {
        'b': 0,
        'a': 1,
        'x': 2,
        'y': 3,
        'l':    4,
        'r':    5,
        'zl':   6,
        'zr':   7,
        'minus':    8,
        'plus':     9,
        'home':     10,
        'l_stick': 11,
        'r_stick': 12,
        # HAT/POV Switches
        # 'up': 13,
        # 'down': 14,
        # 'left': 15,
        # 'right': 16,
    }
    analogs = {
        # [horizontal axis, vertical axis] for analog sticks
        'l_stick_analog': [0, 1],
        'r_stick_analog': [2, 3],
        'l_stick_hat': [4, 5],
        'r_stick_hat': [6, 7],
    }
    buttons = dict((val, key) for key, val in buttons.items())
    button_id = -1
    list_buttons = list(buttons.keys())
    list_analogs = list(analogs.keys())
    while True:
        event = pygame.event.wait()
        if DEBUG:
            print("[user_event]", event)
        try:
            if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                for button_id in list_buttons:
                    val = joystick.get_button(button_id)
                    button_update(buttons[button_id], val)
            elif event.type == pygame.JOYHATMOTION:
                x, y = joystick.get_hat(0)
                if x == 0:  # left/right is unpressed
                    button_update('left', 0)
                    button_update('right', 0)
                elif x == 1:  # right is pressed
                    button_update('right', 1)
                elif x == -1:  # left is pressed
                    button_update('left', 1)
                if y == 0:  # up/down is unpressed
                    button_update('up', 0)
                    button_update('down', 0)
                elif y == 1:  # up is pressed
                    button_update('up', 1)
                elif y == -1:  # down is pressed
                    button_update('down', 1)
            elif event.type == pygame.JOYAXISMOTION:
                for key in list_analogs:
                    val_h = (joystick.get_axis(analogs[key][0]) + 1) / 2
                    val_v = (-joystick.get_axis(analogs[key][1]) + 1) / 2
                    if val_h < 0.1 or val_v < 0.1:
                        continue
                    vals = {}
                    # inputs = [-1, +1]
                    # converts to the range of [0, 4096)
                    vals['h'] = max(int(val_h * 4096) - 1, 0)
                    # converts to the range of [0, 4096) + inversion of the vertical axis
                    vals['v'] = max(int(val_v * 4096) - 1, 0)
                    # inversion might be an issue for other controllers...
                    stick_update(key, vals)
        except pygame.error as e:
            print("Processing button ID ", button_id)
            raise e


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Control-C detected. Bye")
        pass
