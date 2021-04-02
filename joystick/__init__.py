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

    def __iter__(self):
        return (self.timestamp, self.value, self.type, self.number)


EVENT_BUTTON = 0x01
EVENT_AXIS = 0x02
EVENT_INIT = 0x80


# u32 time, s16 val, u8 type, u8 num
EVENT_FORMAT = "=LhBB"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)


async def joystick_poll(id):
    async with aiofiles.open(f"/dev/input/js{id}", mode="rb") as joystick:
        event = bytearray(EVENT_SIZE)
        while True:
            num_bytes_read = await joystick.readinto(event)
            if num_bytes_read <= 0:
                break
            event_time, event_value, event_type, event_number = struct.unpack(
                EVENT_FORMAT, event)
            yield JoystickEvent(event_time, event_value, event_type, event_number)
