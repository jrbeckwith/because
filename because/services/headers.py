"""Define HTTP request headers used in common across service definitions.
"""
from because.headers import Headers

# Headers we send by default across all services, endpoints and methods.
DEFAULT_HEADERS = Headers.coerce({
    b"User-Agent": b"Because",
    b"Accept": b"application/json",
    b"Accept-Charset": b"utf-8",

    # This is not always true because there's not always a body, right?
    # b"Content-Type": b"application/json",
})
