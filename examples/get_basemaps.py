from because import Because
from example_args import get_args
from example_logging import configure_logging


def main():
    args = get_args("Get a list of basemaps.")
    log = configure_logging(debug=args.debug)
    because = Because(env=args.env, log=log)
    because.login(args.username, args.password).wait()

    basemaps = because.basemaps().wait()
    for basemap in basemaps.values():
        print("Basemap {}: {}".format(basemap.title, basemap.url))

    basemap = because.basemap(u"Boundless Basemap").wait()
    print("Basemap {}: {}".format(basemap.title, basemap.url))


main()
