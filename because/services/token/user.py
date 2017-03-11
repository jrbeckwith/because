"""Represent metadata from the payload of a JWT token.
"""

class User(object):
    def __init__(self, email, roles=None):
        self.email = email
        self.roles = set(roles or [])
