from typing import List, Union, Any, Callable, Dict
from .trace_point import TracePoint

class Component():
    def __init__(self, route):
        self.__latency = Latency(route, [])

    @property
    def publishes(self):
        if len(self.__latency.child) == 0:
            return self.__latency.head.publishes + self.__latency.tail.publishes
        return Util.flatten([child.publishes for child in self.__latency.child])

    @property
    def subscribes(self):
        if len(self.__latency.child) == 0:
            return self.__latency.head.subscribes + self.__latency.tail.subscribes
        return Util.flatten([child.subscribes for child in self.__latency.child])

    @property
    def latency(self):
        return self.__latency

    @property
    def timers(self):
        if len(self.__latency.child) == 0:
            return self.__latency.head.timers + self.__latency.tail.timers
        return Util.flatten([child.timers for child in self.__latency.child])

class TraceRoute:
    def __init__(self, head: Union[TracePoint], tail: Union[TracePoint]):
        self.__head = head
        self.__tail = tail

    @property
    def head(self):
        return self.__head

    @property
    def tail(self):
        return self.__tail


class Latency:
    def __init__(self, route: Union[TraceRoute], child: List[Union[Component]]):
        self.__hist = None
        self.__route = route
        self.__child = child
        self.__timeseries = None

    def has_timeseries():
        return self.__timeseries is not None
    @property
    def hist(self):
        return self.__hist
    @hist.setter
    def hist(self, hist):
        self.__hist = hist
    @property
    def timeseries(self):
        return self.__timeseries
    @timeseries.setter
    def timeseries(self, timeseries):
        self.__timeseries = timeseries

    @property
    def route(self):
        return self.__route

    @property
    def child(self):
        return self.__child

    @property
    def head(self):
        return self.__route.head

    @property
    def tail(self):
        return self.__route.tail


class System():
    def __init__(self):
        self.__components = []

    @property
    def subscribes(self):
        pass

    @property
    def publishes(self):
        pass

    def add_component(self, component):
        self.__components.append(component)

    def get_components(self, f):
        components = []
        for component in self.__components:
            if f(component):
                components.append(component)
        return components
