from because.response import parse_json
from . route import (
    Route,
    Leg,
    Step,
    InvalidObject,
)


def parse(response):
    data = parse_json(response, ["distance", "duration", "legs"])
    return dict_to_route(data)


def dict_to_route(data, parse_path=None):
    parse_path = parse_path or []

    try:
        distance = data["distance"]
        duration = data["duration"]
    except KeyError:
        raise InvalidObject("route", data, parse_path=parse_path)
    legs = []
    for index, leg_dict in enumerate(data["legs"]):
        leg = dict_to_leg(
            leg_dict, parse_path=parse_path + ["legs", index]
        )
        legs.append(leg)
    return Route(
        legs=legs,
        distance=distance,
        duration=duration,
    )


def dict_to_leg(data, parse_path=None):
    parse_path = parse_path or []
    try:
        steps = data["steps"]
        distance = data["distance"]
        duration = data["duration"]
    except KeyError:
        raise InvalidObject("leg", parse_path=parse_path)
    steps = [
        dict_to_step(step_dict, parse_path=parse_path + ["steps", index])
        for index, step_dict in enumerate(steps)
    ]
    return Leg(
        steps=steps,
        distance=distance,
        duration=duration,
    )


def dict_to_step(data, parse_path=None):
    parse_path = parse_path or []
    try:
        instructions = data["instructions"]
        distance = data["distance"]
        duration = data["duration"]
        point_data = data["geometry"]
    except KeyError:
        raise InvalidObject("step", parse_path=parse_path)
    except UnicodeEncodeError as error:
        # TODO: this is really serious
        raise InvalidObject("step", parse_path=parse_path)
    try:
        if point_data:
            # NOTE: the "geometry" passed is one big blob of text...
            points = parse_points(
                point_data,
                parse_path=parse_path + ["points"]
            )
        else:
            points = None
    except InvalidObject as error:
        raise InvalidObject("step", parse_path=error.parse_path)

    return Step(
        instructions=instructions,
        points=points,
        distance=distance,
        duration=duration,
    )


def parse_points(data, parse_path=None):
    parse_path = parse_path or []
    try:
        coordinates = data["coordinates"]
        # TODO get rid of TypeError
    except (KeyError, TypeError):
        parse_path = parse_path + ["coordinates"]
        raise InvalidObject("points", parse_path=parse_path)
    # I guess sometimes we get just [x, y] instead of [[x, y]]. :(
    if coordinates and isinstance(coordinates[0], float):
        coordinates = [coordinates]
    return coordinates
