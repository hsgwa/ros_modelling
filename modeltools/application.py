from typing import List, Union, Any, Callable, Dict
from .latency import Latency, System, Component, TraceRoute
from .trace_point import TracePoint
from .data_reader import Histogram, DataReaderFactory
from .util import Util
from .node import Node

class Communication(Component):
    def __init__(self, name: Union[str], route):
        super().__init__(route)
        self.__name = name
        self.__publisher_node = None
        self.__subscriber_node = None

    @property
    def name(self):
        return self.__name

    @property
    def subscribe(self):
        return self.latency.tail.points[0]

    @property
    def publish(self):
        return self.latency.head.points[0]

    @property
    def publisher_node(self):
        return self.__publisher_node

    @publisher_node.setter
    def publisher_node(self, publisher_node):
        self.__publisher_node = publisher_node

    @property
    def subscriber_node(self):
        return self.__subscriber_node

    @subscriber_node.setter
    def subscriber_node(self, subscriber_node):
        self.__subscriber_node = subscriber_node

class Application(System):
    def __init__(self):
        self.__nodes = []
        self.__communications = []
        super().__init__()

    @property
    def subscribes(self):
        return Util.flatten([node.subscribes for node in self.__nodes])

    @property
    def publishes(self):
        return Util.flatten([node.publishes for node in self.__nodes])

    @property
    def timers(self):
        return Util.flatten([node.timers for node in self.__nodes])

    def __update_comms(self, pub, sub):
        if pub.name == sub.name:
            start_point = TracePoint([pub])
            end_point = TracePoint([sub])

            route = TraceRoute(start_point, end_point)
            communication = Communication(pub.name, route)
            communication.publisher_node = self.get_nodes(
                lambda x: communication.publish in x.publishes)[0]
            communication.subscriber_node = self.get_nodes(
                lambda x: communication.subscribe in x.subscribes)[0]
            self.__communications.append(communication)
            super().add_component(communication)

    @property
    def latencies(self):
        starts = list(filter(lambda x: x.start, self.__nodes))
        components = []
        self.__search_node_routes(starts, components, [])
        return [self.to_latency(_) for _ in components]

    def add_node(self, node_):
        self.__nodes.append(node_)
        super().add_component(node_)
        for pub in node_.publishes:
            for sub in self.subscribes:
                self.__update_comms(pub, sub)
        for sub in node_.subscribes:
            for pub in self.publishes:
                self.__update_comms(pub, sub)

    @property
    def nodes(self):
        return self.__nodes

    @property
    def communications(self):
        return self.__communications

    @property
    def subscribes(self):
        return Util.flatten([node.subscribes for node in self.__nodes])

    @property
    def publishes(self):
        return Util.flatten([node.publishes for node in self.__nodes])

    def __search_node_routes(self, depends, routes, route):
        for depend in depends:
            for publish in depend.publishes:
                depends_ = list(filter(lambda x: x.publish ==
                                       publish, self.communications))
                if len(depends) == 0:
                    continue
                route_ = route + [depend]
                self.__search_communication_routes(depends_, routes, route_)

    def __is_valid_route(self, route):
        for i, component in enumerate(route):
            if isinstance(component, Communication) or i == 0 or i == len(route)-1:
                continue
            input_name = route[i-1].name
            node = route[i]
            output_name = route[i+1].name
            if node.is_valid_route(input_name, output_name) == False:
                return False
        return True

    def __search_communication_routes(self, depends, routes, route):
        for depend in depends:
            for node in self.nodes:
                depends_ = list(
                    filter(lambda x: x == depend.subscribe, node.subscribes))
                if len(depends_) == 0:
                    continue
                route_ = route + [depend]
                self.__search_node_routes([node], routes, route_)
                route_ = route + [depend] + [node]
                if node.end and self.__is_valid_route(route_):
                    routes.append(route_)

    def to_latency(self, components_):
        from copy import copy
        components = []
        for idx, component in enumerate(components_):
            pre_component = None if idx-1 < 0 else components[idx-1]
            post_component = None if idx + \
                1 > len(components)-1 else components[idx+1]
            if isinstance(component, Communication):
                components.append(component)
            if isinstance(component, Node):
                latencies = component.latencies
                if post_component is not None:
                    latencies = list(
                        filter(lambda x: post_component.publish in x.tail.publishes, latencies))
                if pre_component is not None:
                    latencies = list(
                        filter(lambda x: pre_component.subscribe in x.head.subscribes, latencies))
                node_ = copy(component)
                node_.latency = latencies[0]
                components.append(node_)
        route = TraceRoute(
            components[0].latency.head, components[-1].latency.tail)
        latency = Latency(route, components)
        latency.hist = Histogram.sum([_.latency.hist for _ in components])
        return latency

    def get_nodes(self, f):
        node = []
        for node_ in self.nodes:
            if f(node_):
                node.append(node_)
        return node

    def set_latency(self, communication_json):
        for communication in self.communications:
            if communication.publisher_node.name == communication_json['publisher'] and \
               communication.subscriber_node.name == communication_json['subscriber'] and \
               communication.name == communication_json['topic_name']:
                reader = DataReaderFactory.create(Util.ext(communication_json['latency']), communication_json['latency_type'])
                communication.latency.hist = reader.get_hist(communication_json['latency'])
                communication.latency.timeseries = reader.get_timeseries(communication_json['latency'])

