import os
import sys
import argparse


def get_base_parser():
    """Get an ArgumentParser which knows how to parse args for auth0 login.

    This isn't used directly, it is used as a "parent" passed to
    ArgumentParser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--env",
        default=os.environ.get("BCS_ENVIRONMENT", "dev"),
        help="environment to use, e.g. 'dev' or 'test'"
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("BCS_USERNAME"),
        help="auth0 username used to get a token"
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("BCS_PASSWORD"),
        help="auth0 password used to get a token"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug output, e.g. to see HTTP requests"
    )
    return parser


def get_parser(description, epilog):
    """Get an ArgumentParser.
    """
    base_parser = get_base_parser()
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        parents=[base_parser],
    )
    return parser


def environ_data(environ):
    mapping = {
        "env": "BCS_ENVIRONMENT",
        "username": "BCS_USERNAME",
        "password": "BCS_PASSWORD",
    }
    data = {
        key: environ.get(value)
        for key, value in mapping.items()
    }
    return data


def get_args(description=None, epilog=None):
    """Get arguments from command line or environment in one call.
    """
    parser = get_parser(description, epilog)
    argv = sys.argv[1:]
    args = parser.parse_args(argv)
    if not args.username or not args.password:
        print("Username and/or password were not specified.")
        parser.print_help()
        sys.exit(1)
        return None
    return args
