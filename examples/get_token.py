from because import Because
from example_args import get_args
from example_logging import configure_logging


def main():
    args = get_args("Get a token.")
    log = configure_logging(debug=args.debug)
    because = Because(env=args.env, log=log)
    transfer = because.login(args.username, args.password)
    print("Waiting...")
    transfer.wait()
    print("Token:")
    print(because.token.pretty_text(u"  "))


main()
