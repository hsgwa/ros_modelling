from typing import List, Union, Any, Callable, Dict

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

