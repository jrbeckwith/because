from because.services.routing.route import (
    Route,
    Leg,
    Step,
)


def _test_from_dict(cls, data):
    """Assert that cls.from_dict() makes a Route instance with the given data.
    """
    result = cls.from_dict(data)
    for key, expected in data.items():
        obtained = getattr(result, key)
        if isinstance(expected, list):
            obtained = list(obtained)
        assert obtained == expected


class Fixtures(object):
    """Hold some common test fixtures, avoiding repetition across tests.
    """

    # 2 points for each of 4 geometries ~ 4 steps.
    points = [
        [0.0, 1.0],
        [2.0, 3.0],
        [4.0, 5.0],
        [6.0, 7.0],
        [8.0, 9.0],
        [10.0, 11.0],
        [12.0, 13.0],
        [14.0, 15.0],
    ]

    # 1 geometry for each of 4 steps.
    geometries = [
        points[0:2],
        points[2:4],
        points[4:6],
        points[6:8],
    ]

    # 2 steps for each of 2 legs.
    steps = [
        Step(u"a", points=geometries[0]),
        Step(u"b", points=geometries[1]),
        Step(u"c", points=geometries[2]),
        Step(u"d", points=geometries[3]),
    ]

    # 2 legs spanning 8 points.
    legs = [
        Leg(steps=steps[0:2]),
        Leg(steps=steps[2:4]),
    ]


class TestStep(object):
    cls = Step

    def test_points(self):
        """Test step.points
        """
        geometry = list(Fixtures.points)
        instance = self.cls(u"Do something", geometry)
        assert list(instance.points) == Fixtures.points


class TestLeg(object):
    cls = Leg

    def test_steps(self):
        """Test leg.steps
        """
        instance = self.cls(Fixtures.steps)
        assert list(instance.steps()) == Fixtures.steps


class TestRoute(object):
    cls = Route

    def test_legs(self):
        """Test route.legs
        """
        instance = self.cls(Fixtures.legs)
        assert list(instance.legs()) == Fixtures.legs
