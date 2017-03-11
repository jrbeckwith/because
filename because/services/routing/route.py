"""Represent results from the routing service.
"""
from because.utils import is_iterable
from because.errors import InvalidObject as _InvalidObject


class InvalidObject(_InvalidObject):
    """Raised on attempts to create an invalid Route, Leg, Step, etc.
    """

    def __init__(self, label, parse_path):
        self.label = label
        self.parse_path = parse_path



class Route(object):
    """A travel route.
    """
    def __init__(self, legs, distance=None, duration=None):
        """
        :arg steps:
            List of Step instances making up the body of the route.
        """
        if not legs or not is_iterable(legs):
            raise InvalidObject("no legs provided")
        self._legs = tuple(legs)
        self.distance = distance
        self.duration = duration

    def legs(self):
        for leg in self._legs:
            yield leg


class Leg(object):
    """One leg of a travel route.
    """
    def __init__(self, steps, distance=None, duration=None):
        """
        :arg steps:
            List of Step instances making up the body of the route.
        """
        if not steps or not is_iterable(steps):
            raise InvalidObject("no steps provided")
        self._steps = steps
        self.distance = distance
        self.duration = duration

    def steps(self):
        for step in self._steps:
            yield step


class Step(object):
    """One step of a leg of a travel route.
    """
    def __init__(self, instructions, points, distance=None, duration=None):
        """
        :arg instructions:
            Text instructions for traveling this step in the route.
        :arg points:
            List of points representing the geometry of this step.
        """
        self.instructions = instructions
        self._points = points
        self.distance = distance
        self.duration = duration

    @property
    def points(self):
        return list(self._points)
