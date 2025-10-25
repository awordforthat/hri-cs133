import asyncio
from enum import Enum
from state import State


class StateName(Enum):
    INITIAL = "initial"
    TRAVELING = "traveling"
    TERMINAL = "terminal"


class Initial(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        pass

    async def execute(self):
        await asyncio.sleep(5)
        return StateName.TRAVELING

    async def stop(self):
        pass


class Traveling(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        pass

    async def execute(self):
        print("executing travel")
        await asyncio.sleep(5)
        return StateName.TERMINAL

    async def stop(self):
        pass


class Terminal(State):
    def __init__(self, sphero, name):
        super().__init__(sphero, name)

    async def start(self):
        print("Starting terminal")

    async def execute(self):
        print("executing terminal")

    async def stop(self):
        print("stopping terminal")
