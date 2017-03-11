from because.request import Request
from because.interfaces.python.client import Client


def main():
    client = Client()
    request = Request(b"GET", b"https://www.google.com")
    transfer = client.send(request)
    response = transfer.wait()
    print(response)
    print(response.body)


main()
