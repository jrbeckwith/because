from because import Because
from example_args import get_args
from example_logging import configure_logging


def main():
    args = get_args("Geocode an address.")
    log = configure_logging(debug=args.debug)
    because = Because(env=args.env, log=log)
    because.login(args.username, args.password).wait()

    address = "1600 Pennsylvania Ave., Washington, DC"
    matches = because.geocode(address, service="mapbox").wait()
    for index, match in enumerate(matches):
        print("Match {}:".format(index))
        print(
            """
            Score: {}
            Location: ({}, {})
            Address: {}
            """.format(match.score, match.x, match.y, match.address),
        )


main()
