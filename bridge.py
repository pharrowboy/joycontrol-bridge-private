#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
import sys
import time

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


dirty = False


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
        dirty = True
    logger.info("Polling Ended")


async def send_at_60Hz(protocol):
    while True:
        if dirty:
            start = time.time()
            if not await protocol.flush():
                return
            end = time.time()
            sleep = 0.0166666667 - (end - start)
            await asyncio.sleep(max(sleep, 0))
    logger.info("Synchronization Ended")


async def monitor_throughput(throughput):
    while True:
        await asyncio.sleep(3)
        throughput.update()
        logger.info("{} Packets/sec".format(throughput.counts_sec))


async def _main(args):
    with utils.get_output(path=args.log, default=None) as capture_file:
        factory = controller_protocol_factory(
            Controller.PRO_CONTROLLER, spi_flash=FlashMemory())
        ctl_psm, itr_psm = 17, 19
        transport, protocol = await create_hid_server(factory, reconnect_bt_addr=args.reconnect_bt_addr,
                                                      ctl_psm=ctl_psm,
                                                      itr_psm=itr_psm, capture_file=capture_file,
                                                      device_id=args.device_id)
        controller_state = protocol.get_controller_state()
        await controller_state.connect()
        logger.info("Connected!")
        # slow down reading
        protocol.frequency.value = 0.3

        asyncio.ensure_future(monitor_throughput(protocol.throughput))

        try:
            await relais(protocol, controller_state)
        finally:
            logger.info('Stopping communication...')
            await transport.close()


if __name__ == '__main__':
    # check if root
    if not os.geteuid() == 0:
        raise PermissionError('Script must be run as root!')

    # setup logging
    log.configure()

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log')
    parser.add_argument('-d', '--device_id')
    parser.add_argument('-r', '--reconnect_bt_addr', type=str, default=None,
                        help='The Switch console Bluetooth address, for reconnecting as an already paired controller')
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main(args))
