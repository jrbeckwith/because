class Candidate(object):
    def __init__(
            self,
            x,
            y,
            address,
            score=None,
            source=None,
    ):
        self.x = x
        self.y = y
        self.address = address
        self.score = score
        self.source = source
