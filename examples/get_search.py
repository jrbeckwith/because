from because import Because
from example_args import get_args
from example_logging import configure_logging


def main():
    args = get_args("Do some searches.")
    log = configure_logging(debug=args.debug)
    because = Because(env=args.env, log=log)
    because.login(args.username, args.password).wait()

    categories = because.search_categories().wait()
    for key, category in categories.items():
        print("Category {}: {}".format(category.key, category.description))

    results = because.search_category("DOC", "geoserver").wait()
    for index, result in enumerate(results, 1):
        print("Result {}: {}".format(index, result.title))
        print("    {}".format(result.url))
        print()

    results = because.opensearch("geoserver").wait()
    for index, result in enumerate(results, 1):
        print("Result {}: {}".format(index, result.title))
        print("    {}".format(result.url))
        print()


main()
