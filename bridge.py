#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os

import pygame
import sys
import time

from aioconsole import ainput

from joycontrol import logging_default as log, utils
from joycontrol.command_line_interface import ControllerCLI
from joycontrol.controller import Controller
from joycontrol.controller_state import ControllerState, button_push, button_update
from joycontrol.memory import FlashMemory
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server

logger = logging.getLogger(__name__)

"""Emulates Switch controller. Opens joycontrol.command_line_interface to send button commands and more.

While running the cli, call "help" for an explanation of available commands.

Usage:
    run_controller_cli.py <controller> [--device_id | -d  <bluetooth_adapter_id>]
                                       [--spi_flash <spi_flash_memory_file>]
                                       [--reconnect_bt_addr | -r <console_bluetooth_address>]
                                       [--log | -l <communication_log_file>]
    run_controller_cli.py -h | --help

Arguments:
    controller      Choose which controller to emulate. Either "JOYCON_R", "JOYCON_L" or "PRO_CONTROLLER"

Options:
    -d --device_id <bluetooth_adapter_id>   ID of the bluetooth adapter. Integer matching the digit in the hci* notation
                                            (e.g. hci0, hci1, ...) or Bluetooth mac address of the adapter in string
                                            notation (e.g. "FF:FF:FF:FF:FF:FF").
                                            Note: Selection of adapters may not work if the bluez "input" plugin is
                                            enabled.

    --spi_flash <spi_flash_memory_file>     Memory dump of a real Switch controller. Required for joystick emulation.
                                            Allows displaying of JoyCon colors.
                                            Memory dumps can be created using the dump_spi_flash.py script.

    -r --reconnect_bt_addr <console_bluetooth_address>  Previously connected Switch console Bluetooth address in string
                                                        notation (e.g. "FF:FF:FF:FF:FF:FF") for reconnection.
                                                        Does not require the "Change Grip/Order" menu to be opened,

    -l --log <communication_log_file>       Write hid communication (input reports and output reports) to a file.
"""
def get_button(joystick):
    # todo: - hats
    for event in pygame.event.get(): # User did something.
        if event.type == pygame.JOYBUTTONDOWN:
                buttons = joystick.get_numbuttons()
                for i in range(buttons):
                    button = joystick.get_button(i)
                    if button == 1:
                        return i
        if event.type == pygame.JOYBUTTONUP:
            None    

    '''
    hats = joystick.get_numhats()
    for i in range(hats):
        hat = joystick.get_hats(i)
        for j in range(2): 
            if hat[j] != 0:
                return [j, True] # return number of the button and if it's a hat key (True) or normal key (False)
    '''

def init_relais():
    # todo: - analog to button conversion
    #       - analog axis

    pygame.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    button_strings = ['a', 'b', 'x', 'y', 'up', 'down', 'left', 'right', 'minus', 'plus', 'home', 'capture', 'l', 'r', 'zl', 'zr', 'l_stick', 'r_stick']
    '''
    0 - B
    1 - A
    2 - Y
    3 - X
    4 - L
    5 - R
    6 - Minus
    7 - Plus
    8 - Home
    9 - l_stick
    10 - r_stick
    '''

    '''
    buttons = {}    
    for button in button_strings:
        pressed = 0
        print("Press {0}".format(button))        
        while not pressed:
            buttons[button] = get_button(joystick)
            pressed = buttons[button]
        time.sleep(0.5)
    '''
    buttons = {
        'a': 1,
        'b': 0,
        'x': 3,
        'y': 2,
        'up': 8,
        'down': 8,
        'left': 8,
        'right': 8,
        'minus': 6,
        'plus': 7,
        'home': 8,
        'capture': 8,
        'l': 4,
        'r': 5,
        'zl': 8,
        'zr': 8,
        'l_stick': 9,
        'r_stick': 10
    }
    return buttons

async def relais(controller_state):
    buttons = init_relais()
    buttons = dict((val, key) for key, val in buttons.items())
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    while True:
        for event in pygame.event.get(): # User did something.
            if event.type == pygame.JOYBUTTONDOWN:
                None
            elif event.type == pygame.JOYBUTTONUP:
                None        

        for button_id in list(buttons.keys()):        
            val = joystick.get_button(button_id)
            await button_update(controller_state, buttons[button_id], val)

async def test_controller_buttons(controller_state: ControllerState):
    """
    Example controller script.
    Navigates to the "Test Controller Buttons" menu and presses all buttons.
    """
    if controller_state.get_controller() != Controller.PRO_CONTROLLER:
        raise ValueError('This script only works with the Pro Controller!')

    # waits until controller is fully connected
    await controller_state.connect()

    await ainput(prompt='Make sure the Switch is in the Home menu and press <enter> to continue.')

    """
    # We assume we are in the "Change Grip/Order" menu of the switch
    await button_push(controller_state, 'home')

    # wait for the animation
    await asyncio.sleep(1)
    """

    # Goto settings
    await button_push(controller_state, 'down', sec=1)
    await button_push(controller_state, 'right', sec=2)
    await asyncio.sleep(0.3)
    await button_push(controller_state, 'left')
    await asyncio.sleep(0.3)
    await button_push(controller_state, 'a')
    await asyncio.sleep(0.3)

    # go all the way down
    await button_push(controller_state, 'down', sec=4)
    await asyncio.sleep(0.3)

    # goto "Controllers and Sensors" menu
    for _ in range(2):
        await button_push(controller_state, 'up')
        await asyncio.sleep(0.3)
    await button_push(controller_state, 'right')
    await asyncio.sleep(0.3)

    # go all the way down
    await button_push(controller_state, 'down', sec=3)
    await asyncio.sleep(0.3)

    # goto "Test Input Devices" menu
    await button_push(controller_state, 'up')
    await asyncio.sleep(0.3)
    await button_push(controller_state, 'a')
    await asyncio.sleep(0.3)

    # goto "Test Controller Buttons" menu
    await button_push(controller_state, 'a')
    await asyncio.sleep(0.3)

    # push all buttons except home and capture
    button_list = controller_state.button_state.get_available_buttons()
    if 'capture' in button_list:
        button_list.remove('capture')
    if 'home' in button_list:
        button_list.remove('home')

    user_input = asyncio.ensure_future(
        ainput(prompt='Pressing all buttons... Press <enter> to stop.')
    )

    # push all buttons consecutively until user input
    while not user_input.done():
        for button in button_list:
            await button_push(controller_state, button)
            await asyncio.sleep(0.1)

            if user_input.done():
                break

    # await future to trigger exceptions in case something went wrong
    await user_input

    # go back to home
    await button_push(controller_state, 'home')


async def set_amiibo(controller_state, file_path):
    """
    Sets nfc content of the controller state to contents of the given file.
    :param controller_state: Emulated controller state
    :param file_path: Path to amiibo dump file
    """
    loop = asyncio.get_event_loop()

    with open(file_path, 'rb') as amiibo_file:
        content = await loop.run_in_executor(None, amiibo_file.read)
        controller_state.set_nfc(content)


async def mash_button(controller_state, button, interval):
    # waits until controller is fully connected
    await controller_state.connect()

    if button not in controller_state.button_state.get_available_buttons():
        raise ValueError(f'Button {button} does not exist on {controller_state.get_controller()}')

    user_input = asyncio.ensure_future(
        ainput(prompt=f'Pressing the {button} button every {interval} seconds... Press <enter> to stop.')
    )
    # push a button repeatedly until user input
    while not user_input.done():
        await button_push(controller_state, button)
        await asyncio.sleep(float(interval))

    # await future to trigger exceptions in case something went wrong
    await user_input


async def _main(args):
    # parse the spi flash
    if args.spi_flash:
        with open(args.spi_flash, 'rb') as spi_flash_file:
            spi_flash = FlashMemory(spi_flash_file.read())
    else:
        # Create memory containing default controller stick calibration
        spi_flash = FlashMemory()

    # Get controller name to emulate from arguments
    controller = Controller.from_arg(args.controller)

    with utils.get_output(path=args.log, default=None) as capture_file:
        factory = controller_protocol_factory(controller, spi_flash=spi_flash)
        ctl_psm, itr_psm = 17, 19
        transport, protocol = await create_hid_server(factory, reconnect_bt_addr=args.reconnect_bt_addr,
                                                      ctl_psm=ctl_psm,
                                                      itr_psm=itr_psm, capture_file=capture_file,
                                                      device_id=args.device_id)

        controller_state = protocol.get_controller_state()

        # Create command line interface and add some extra commands
        cli = ControllerCLI(controller_state)

        # Wrap the script so we can pass the controller state. The doc string will be printed when calling 'help'
        async def _run_test_controller_buttons():
            """
            test_buttons - Navigates to the "Test Controller Buttons" menu and presses all buttons.
            """
            await test_controller_buttons(controller_state)

        # add the script from above
        cli.add_command('test_buttons', _run_test_controller_buttons)

        # init_relais command
        async def _run_init_relais():
            """
            init_relais - init the relais and configure button layout
            """
            init_relais()

        # add the script from above
        cli.add_command('init_relais', _run_init_relais)

        # relais command
        async def _run_relais():
            """
            relais - run the relais
            """
            await relais(controller_state)

        # add the script from above
        cli.add_command('relais', _run_relais)

        # Mash a button command
        async def call_mash_button(*args):
            """
            mash - Mash a specified button at a set interval

            Usage:
                mash <button> <interval>
            """
            if not len(args) == 2:
                raise ValueError('"mash_button" command requires a button and interval as arguments!')

            button, interval = args
            await mash_button(controller_state, button, interval)

        # add the script from above
        cli.add_command('mash', call_mash_button)

        # Create amiibo command
        async def amiibo(*args):
            """
            amiibo - Sets nfc content

            Usage:
                amiibo <file_name>          Set controller state NFC content to file
                amiibo remove               Remove NFC content from controller state
            """
            if controller_state.get_controller() == Controller.JOYCON_L:
                raise ValueError('NFC content cannot be set for JOYCON_L')
            elif not args:
                raise ValueError('"amiibo" command requires file path to an nfc dump as argument!')
            elif args[0] == 'remove':
                controller_state.set_nfc(None)
                print('Removed nfc content.')
            else:
                await set_amiibo(controller_state, args[0])

        # add the script from above
        cli.add_command('amiibo', amiibo)

        try:
            await cli.run()
        finally:
            logger.info('Stopping communication...')
            await transport.close()


if __name__ == '__main__':
    # check if root
    if not os.geteuid() == 0:
        raise PermissionError('Script must be run as root!')

    # setup logging
    #log.configure(console_level=logging.ERROR)
    log.configure()

    parser = argparse.ArgumentParser()
    parser.add_argument('controller', help='JOYCON_R, JOYCON_L or PRO_CONTROLLER')
    parser.add_argument('-l', '--log')
    parser.add_argument('-d', '--device_id')
    parser.add_argument('--spi_flash')
    parser.add_argument('-r', '--reconnect_bt_addr', type=str, default=None,
                        help='The Switch console Bluetooth address, for reconnecting as an already paired controller')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _main(args)
    )
