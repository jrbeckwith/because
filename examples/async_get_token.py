import asyncio
from because import Because
from example_args import get_args
from example_logging import configure_logging


async def run(env, username, password):
    because = Because("concurrent", env)
    transfer = because.login(username, password)
    print("Waiting...")
    token = await transfer
    print("Token:")
    print(token.pretty_text(u"  "))


def main():
    args = get_args("Get a token.")
    configure_logging(debug=args.debug)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(args.env, args.username, args.password))
    loop.close()


main()
