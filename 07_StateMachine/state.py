from abc import ABC, abstractmethod


class State(ABC):
    def __init__(self, sphero, name):
        self.sphero = sphero
        self.name = name

    @abstractmethod
    async def start(self):
        raise NotImplementedError()

    @abstractmethod
    async def execute(self):
        raise NotImplementedError()

    @abstractmethod
    async def stop(self):
        raise NotImplementedError()
