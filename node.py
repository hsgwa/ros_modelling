from typing import List, Union, Any, Callable, Dict
from .latency import Latency, System, Component, TraceRoute
from .histogram import Histogram
from .trace_point import TracePoint, Timer, Publish, Subscribe
from .callback import Callback, TimerCallback, SubscribeCallback
from .util import Util

class Execution(Component):
    pass

class Node(System):
    def __init__(self, name, start=False, end=False, latency=None):
        super().__init__()
        self.__latency = latency
        self.__name = name
        self.__start = start
        self.__end = end
        self.__callbacks = []
        self.__executions = []
    @classmethod
    def create(cls, histogram_reader, node_json):
        node = Node(node_json['name'])
        if 'start_node' in node_json.keys():
            node.start = node_json['start_node']
        if 'end_node' in node_json.keys():
            node.end = node_json['end_node']
        for callback_json in node_json['callbacks']:

            start_point = TracePoint()
            end_point = TracePoint()

            if callback_json['type'] == 'subscribe':
                topic_name = callback_json['topic_name']
                start_point.add(Subscribe(topic_name))
            if callback_json['type'] == 'timer':
                start_point.add(Timer())

            if 'publish' in callback_json.keys():
                for publish in callback_json['publish']:
                    topic_name = publish['topic_name']
                    end_point.add(Publish(topic_name))
            route = TraceRoute(start_point, end_point)
            callback = Callback.create(
                callback_json['type'], callback_json['name'], route=route)
            callback.latency.hist = histogram_reader.read(
                callback_json['latency'])
            node.add_callback(callback)

        if 'execution' in node_json.keys():
            for execution_ in node_json['execution']:
                start_point = node.find_callback(
                    name=execution_['from']).latency.tail
                end_point = node.find_callback(
                    name=execution_['to']).latency.head
                route = TraceRoute(start_point, end_point)
                execution = Execution(route)
                execution.latency.hist = histogram_reader.read(execution_[
                                                               'latency'])
                node.add_execution(execution)

        return node

    @property
    def start(self):
        return self.__start

    @start.setter
    def start(self, start):
        self.__start = start

    @property
    def end(self):
        return self.__end

    @end.setter
    def end(self, end):
        self.__end = end

    @property
    def latency(self):
        return self.__latency

    @latency.setter
    def latency(self, latency):
        self.__latency = latency

    @property
    def latencies(self):
        inputs = []
        inputs += super().get_components(lambda x: isinstance(x, TimerCallback))
        inputs += super().get_components(lambda x: isinstance(x, SubscribeCallback))
        child = []
        self.__search_routes(inputs, child, [])
        return [self.__to_latency(_) for _ in child]

    @property
    def subscribes(self):
        return Util.flatten([callback.subscribes for callback in self.__callbacks])

    @property
    def publishes(self):
        return Util.flatten([callback.publishes for callback in self.__callbacks])

    @property
    def timers(self):
        return Util.flatten([callback.timers for callback in self.__callbacks])

    @property
    def name(self):
        return self.__name

    @property
    def callbacks(self):
        return self.__callbacks

    @property
    def executions(self):
        return self.__executions

    def __search_routes(self, depends, routes, components):
        if depends == []:
            return

        for depend in depends:
            if depend.latency.tail.has_publish() or self.end:
                routes.append(components + [depend])
            depends_ = super().get_components(lambda x: x.latency.head == depend.latency.tail)
            self.__search_routes(depends_, routes, components + [depend])

    def __to_latency(self, child):
        route = TraceRoute(child[0].latency.head, child[-1].latency.tail)
        latency = Latency(route, child)
        latency.hist = Histogram.sum([_.latency.hist for _ in child])
        return latency

    def add_execution(self, execution: Union[Execution]):
        super().add_component(execution)
        self.__executions.append(execution)

    def add_callback(self, callback: Union[Callback]):
        super().add_component(callback)
        self.__callbacks.append(callback)

    def find_callback(self, name):
        for callback in self.__callbacks:
            if callback.name == name:
                return callback
        return None

    def is_valid_route(self, in_name=None, out_name=None):
        for latency in self.latencies:
            if (in_name is not None and in_name in [_.name for _ in latency.head.subscribes]) and \
               (out_name is not None and out_name in [_.name for _ in latency.tail.publishes]):
                return True
        return False

