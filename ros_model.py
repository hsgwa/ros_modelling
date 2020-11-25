from typing import List, Union, Any, Callable, Dict
import numpy as np


class Util():
    @classmethod
    def flatten(cls, x):
        import itertools
        return list(itertools.chain.from_iterable(x))


class TracePointComponent:
    pass


class TracePoint:
    def __init__(self, points=[]):
        if len(points) == 0:
            self.__trace_points = [self]
        else:
            self.__trace_points = points

    def has_publish(self, name=''):
        if name == '' and len(self.publishes) > 0:
            return True
        for pub in self.publishes:
            if name in pub.names:
                return True
        return False

    def has_subscribe(self, name=''):
        if name == '' and len(self.subscribes) > 0:
            return True
        for sub in self.subscribes:
            if name in sub.names:
                return True
        return False

    def add(self, component: Union[TracePointComponent]):
        self.__trace_points.append(component)

    @property
    def points(self):
        return self.__trace_points

    @property
    def timers(self):
        timers = []
        for point in self.points:
            if isinstance(point, Timer):
                timers.append(point)
        return timers

    @property
    def publishes(self):
        publishes = []
        for point in self.points:
            if isinstance(point, Publish):
                publishes.append(point)
        return publishes

    @property
    def subscribes(self):
        subscribes = []
        for point in self.points:
            if isinstance(point, Subscribe):
                subscribes.append(point)
        return subscribes

    def __eq__(self, trace_point):
        for point in self.__trace_points:
            for point_ in trace_point.points:
                if point is point_:
                    return True
        return False

    def __add__(self, trace_point):
        return TracePoint(trace_point.points + self.__trace_points)


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


class Histogram:
    __normalize = False

    def __init__(self, raw: Union[np.array]):
        if Histogram.__normalize:
            raw = raw / np.sum(raw)
        self.__raw = raw

    @classmethod
    def normalize(cls, use):
        cls.__normalize = use

    @classmethod
    def get_normalize(cls):
        return cls.__normalize

    @classmethod
    def sum(cls, histgrams):
        hist = Histogram(histgrams[0].raw)
        for histgram in histgrams[1:]:
            hist = hist + histgram
        return hist

    def __add__(self, hist_):
        # todo : length validation
        tmp = np.convolve(self.__raw, hist_.raw, mode='full')
        tmp[len(self.__raw)-1] += np.sum(tmp[len(self.__raw):])  # オーバーした分
        tmp = tmp[:len(self.__raw)]
        if Histogram.__normalize:
            tmp = tmp / np.sum(tmp)
        return self.__class__(tmp)

    @property
    def raw(self) -> np.ndarray:
        return self.__raw


class Timeseries:
    def __init__(self, raw: Union[np.array]):
        self.__raw = raw

    @property
    def raw(self) -> np.ndarray:
        return self.__raw


class HistogramReader:
    def read(self, file_path: Union[str]) -> Histogram:
        pass


class TimeseriesReader:
    def read(self, file_path: Union[str]) -> Histogram:
        pass


class HistogramReaderFactory:
    @classmethod
    def create(cls, reader_type):
        if reader_type == 'csv':
            return CsvHistogramReader()

        return None


class TimeseriesReaderFactory:
    @classmethod
    def create(cls, reader_type):
        if reader_type == 'csv':
            return CsvHistogramReader()
        return None


class CsvTimeseriesReader(TimeseriesReader):
    def read(self, file_path: Union[str]) -> Timeseries:
        self.csv_path = file_path
        data = np.loadtxt(self.csv_path, delimiter=',')
        def to_sec(x): return x[0] + x[1]*1e-9
        data_sec = [to_sec(_) for _ in data]
        return Timeseries(data_sec)


class CsvHistogramReader(HistogramReader):
    def read(self, file_path: Union[str]) -> Histogram:
        self.csv_path = file_path
        data = np.loadtxt(self.csv_path, delimiter=',')
        return Histogram(data.T[1])


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


class Latency:
    def __init__(self, route: Union[TraceRoute], child: List[Union[Component]]):
        self.__hist = None
        self.__route = route
        self.__child = child

    @property
    def hist(self):
        return self.__hist

    @hist.setter
    def hist(self, hist):
        self.__hist = hist

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


class Timer(TracePointComponent):
    pass


class Publish(TracePointComponent):
    def __init__(self, name: Union[str] = ''):
        super().__init__()
        self.__name = name

    @property
    def name(self):
        return self.__name


class Subscribe(TracePointComponent):
    def __init__(self, name: Union[str] = ''):
        super().__init__()
        self.__name = name

    @property
    def name(self):
        return self.__name


class Callback(Component):
    def __init__(self, name: Union[str], route):
        super().__init__(route)
        self.__name = name

    @property
    def name(self):
        return self.__name


class SubscribeCallback(Callback):
    pass


class TimerCallback(Callback):
    pass
# ノード内はExecution。ノード内通信も含む


class Execution(Component):
    pass
# ノード間はCommunication


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


class CallbackFactory():
    @classmethod
    def create(cls, callback_type, name: Union[str], route: Union[TraceRoute]) -> Callback:
        if callback_type == 'timer':
            return TimerCallback(name, route)
        elif callback_type == 'subscribe':
            return SubscribeCallback(name, route)


class NodeFactory():
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
            callback = CallbackFactory.create(
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


class Node(System):
    def __init__(self, name, start=False, end=False, latency=None):
        super().__init__()
        self.__latency = latency
        self.__name = name
        self.__start = start
        self.__end = end
        self.__callbacks = []
        self.__executions = []

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

    def set_latency(self, histogram_reader, communication_json):
        for communication in self.communications:
            if communication.publisher_node.name == communication_json['publisher'] and \
               communication.subscriber_node.name == communication_json['subscriber'] and \
               communication.name == communication_json['topic_name']:
                communication.latency.hist = histogram_reader.read(
                    communication_json['latency'])


class ArchitectureReader:
    @classmethod
    def read(cls, file_path):
        import json
        with open(file_path) as f:
            arch = json.load(f)
        histogram_reader = HistogramReaderFactory.create(arch['latency_type'])

        app = Application()
        for node_json in arch['nodes']:
            app.add_node(NodeFactory.create(histogram_reader, node_json))
        for communication_json in arch['communication']:
            app.set_latency(histogram_reader, communication_json)
        return app
