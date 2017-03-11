from collections import OrderedDict
from because.reprs import ReprMixin
from because.pretty import PrettyMixin


class SearchCategory(ReprMixin, PrettyMixin):
    def __init__(self, key, description, service):
        self.key = key
        self.description = description
        self.service = service

    def search(self):
        pass

    def repr_data(self):
        return OrderedDict({
            "key": self.key,
            "description": self.description,
        })
