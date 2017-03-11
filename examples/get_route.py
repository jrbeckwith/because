from because import Because
from example_args import get_args
from example_logging import configure_logging


def main():
    args = get_args("Get a route.")
    log = configure_logging(debug=args.debug)
    because = Because(env=args.env, log=log)
    because.login(args.username, args.password).wait()

    home = "3637 Far West Blvd, Austin, TX 78731"
    dest = "1600 Pennsylvania Ave., Washington, DC"
    route = because.route(home, dest, service="mapbox").wait()

    for leg_number, leg in enumerate(route.legs()):
        print("Leg {}:".format(leg_number))
        for step_number, step in enumerate(leg.steps()):
            print("Step {}:".format(leg_number))
            print(step.instructions)
            print(step.points)


main()
