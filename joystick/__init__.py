# coding: utf-8

# Lightweight Joystick API
# Usage:
# joystick_poll()

import aiofiles
import enum
import struct


class JoystickEvent:
    def __init__(self, timestamp, value, type, number):
        self.timestamp = timestamp
        self.value = value
        self.type = type
        self.number = number

    def __str__(self):
        return "Time: {} | Value: {} | Type: {} | Number: {}".format(
            self.timestamp, self.value, self.type, self.number)

    def __getitem__(self, key):
        return (self.timestamp, self.value, self.type, self.number)[key]


EVENT_BUTTON = 0x01
EVENT_AXIS = 0x02
EVENT_INIT = 0x80


# u32 time, s16 val, u8 type, u8 num
EVENT_FORMAT = "=LhBB"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)


async def joystick_poll(id):
    async with aiofiles.open(f"/dev/input/js{id}", mode="rb") as joystick:
        event = bytearray(EVENT_SIZE)
        while (await joystick.readinto(event) > 0):
            time, value, type, number = struct.unpack(EVENT_FORMAT, event)
            yield JoystickEvent(time, value, type, number)
