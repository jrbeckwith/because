from because import Because
from example_args import get_args
from example_logging import configure_logging


def main():
    args = get_args("Reverse geocode a location.")
    log = configure_logging(debug=args.debug)
    because = Because(env=args.env, log=log)
    because.login(args.username, args.password).wait()

    x, y = (-76.981041, 38.878649)
    matches = because.reverse_geocode(x, y, service="mapbox").wait()
    for index, match in enumerate(matches):
        print("Match {}:".format(index))
        print(
            """
            Score: {}
            Location: ({}, {})
            Address: {}
            """.format(match.score, match.x, match.y, match.address)
        )


main()
