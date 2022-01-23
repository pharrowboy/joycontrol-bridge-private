#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
import sys
import time
import os
import time
import argparse
import asyncio
import logging

from multiprocessing import Process
from multiprocessing import Queue

from joycontrol import utils
from joycontrol.controller import Controller

from datetime import datetime, timedelta

import aiofiles
import hid
import joystick

from joycontrol import logging_default as log, utils
from joycontrol.controller import Controller
from joycontrol.controller_state import ControllerState
from joycontrol.memory import FlashMemory
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server

logger = logging.getLogger(__name__)


async def init_relais():
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
    if not os.path.exists("/dev/input/js0"):
        logger.warn("Please connect any controller! Waiting...")

    while not os.path.exists("/dev/input/js0"):
        await asyncio.sleep(1)

    logger.info("Controller connected.")
    return buttons, 0


async def relais(protocol, controller_state):
    def normalize(value):
        return max(min(value, 32767), -32767) / 32767

    def clamp(value, minv=0, maxv=4095):
        return min(max(value, minv), maxv)

    buttons, id = await init_relais()
    sticks = (controller_state.l_stick_state, controller_state.r_stick_state)
    logger.info("Polling Joystick...")
    async for event in joystick.joystick_poll(id):
        if protocol.ended:
            break
        _timestamp, value, type, number = event
        if type == joystick.EVENT_BUTTON:
            controller_state.button_state.set_button(buttons[number], value)
        elif type == joystick.EVENT_AXIS:
            is_vertical = (number & 1)
            stick_state = sticks[number // 2]
            axis = normalize(value)
            if is_vertical:
                stick_state.set_v(clamp(int((-axis + 1) / 2 * 4095)))
            else:
                stick_state.set_h(clamp(int((axis + 1) / 2 * 4095)))
        protocol.dirty = True
    logger.info("Polling Ended")


async def send_at_60Hz(protocol):
    delay_base = 0.0166666667
    while True:
        sleep = delay_base
        if protocol.dirty:
            start = time.time()
            if not await protocol.flush():
                return
            end = time.time()
            sleep -= (end - start)
            protocol.dirty = False
        await asyncio.sleep(max(sleep, 0))
    logger.info("Synchronization Ended")


async def monitor_throughput(throughput):
    while True:
        await asyncio.sleep(3)
        throughput.update()
        logger.info("{} Packets/sec".format(throughput.counts_sec))






async def _main(args, c, q, reconnect_bt_addr=None):

    # Get controller name to emulate from arguments
    controller = Controller.PRO_CONTROLLER

    # prepare the the emulated controller
    factory = controller_protocol_factory(controller,
                            reconnect = reconnect_bt_addr)

    ctl_psm, itr_psm = 17, 19

    print('', end='\n' if c else ' ')
    print('  Joy Transfer  v0.1')
    print('INFO: Waiting for Switch to connect...', end='\n' if c else ' ')

    if c < 1:
        print('Please open the "Change Grip/Order" menu')

    transport, protocol, ns_addr = await create_hid_server(factory,
                                                  reconnect_bt_addr=reconnect_bt_addr,
                                                  ctl_psm=ctl_psm,
                                                  itr_psm=itr_psm,
                                                  unpair = not reconnect_bt_addr)
    controller_state = protocol.get_controller_state()

    # this is needed
    await controller_state.connect()

    if not reconnect_bt_addr:
        reconnect_bt_addr = ns_addr
        q.put(ns_addr)

    # wait back home in nintendo switch
    if c < 1:
        print('INFO: NINTENDO SWITCH', reconnect_bt_addr)
        if args.auto:
            controller_state.button_state.set_button('a', pushed=True)
            await controller_state.send()
        else:
            print('INFO: Press the button A or B or HOME')
        print()

        while 1:
            await asyncio.sleep(0.2)
    protocol.frequency.value = 0.3

    asyncio.ensure_future(monitor_throughput(protocol.throughput))
    asyncio.ensure_future(send_at_60Hz(protocol))
    logger.info("Connected!")
       
    try:
        await relais(protocol, controller_state)
    finally:
        logger.info('Stopping communication...')
        await transport.close()
    q.put('unlock') # unlock console
    print('hi :3')


    while 1:
        cmd = q.get() # wait command

        await test_button(controller_state, cmd)
        

'''
NINTENDO SWITCH
    - version 12.1.0
    - version 13.0.0
'''
async def test_button(ctrl, btn):
        available_buttons = ctrl.button_state.get_available_buttons()

        if btn == 'wake':
            # wake up control
            ctrl.button_state.clear()
            await ctrl.send()
            await asyncio.sleep(0.050) # stable minimum 0.050

        if btn not in available_buttons:
            return 1

        ctrl.button_state.set_button(btn, pushed=True)
        await ctrl.send()

        await asyncio.sleep(0.050) # stable minimum 0.050 press
        ctrl.button_state.set_button(btn, pushed=False)
        await ctrl.send()
        await asyncio.sleep(0.020) # stable minimum 0.020 release

        return 0

def handle_exception(loop, context):
    tasks = [t for t in asyncio.all_tasks() if t is not
                         asyncio.current_task()]
    for task in tasks:
        task.cancel()

count = 0

def test(args, c, q, b):
    try:
        loop.run_until_complete(
            _main(args, c, q, b)
        )
    except:
        pass

if __name__ == '__main__':

    # check if root
    if not os.geteuid() == 0:
        raise PermissionError('Script must be run as root!')
    log.configure()

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log')
    parser.add_argument('-d', '--device_id')
    parser.add_argument('--auto', dest='auto', action='store_true')
    parser.add_argument('-r', '--reconnect_bt_addr', type=str, default=None,
                        help='The Switch console Bluetooth address (or "auto" for automatic detection), for reconnecting as an already paired controller.')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

    queue = Queue()

    cmd = None

    ns_addr = args.reconnect_bt_addr
    if ns_addr:
        count = 1

    for _ in range(2 - count):
        p = Process(target=test, args=(args, count, queue, ns_addr))
        p.start()

        if count < 1:
            ns_addr = queue.get() # wait nintendo switch address
            p.join()
        else:
            queue.get() # lock console

        while p.is_alive():
            cmd = input('cmd >> ')
            if cmd in ['exit', 'quit', 'q', 'bye', 'shutdown']:
                p.kill()
                break

            queue.put(cmd)
            time.sleep(0.2) # not needed

        # wait reconnection
        time.sleep(2) # important 2 or more
        count += 1

    print("bye")
