from typing import List, Union, Any, Callable, Dict
from .latency import Component, TraceRoute

class Callback(Component):
    def __init__(self, name: Union[str], route):
        super().__init__(route)
        self.__name = name

    @classmethod
    def create(cls, callback_type, name: Union[str], route: Union[TraceRoute]): 
        if callback_type == 'timer':
            return TimerCallback(name, route)
        elif callback_type == 'subscribe':
            return SubscribeCallback(name, route)

    @property
    def name(self):
        return self.__name


class SubscribeCallback(Callback):
    pass


class TimerCallback(Callback):
    pass
