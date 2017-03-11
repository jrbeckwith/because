from typing import (
    Any,
    List,
    Tuple,
    Text,
)
from collections import OrderedDict


class PrettyMixin(object):
    """Mixin for making it easy to prettyprint a class.

    A pretty print can span lines and doesn't need to be delimited like a repr.
    """

    def pretty_tuples(self):
        # type: () -> List[Tuple[Text, Any]]
        raise NotImplementedError()

    def pretty_dict(self):
        # type: () -> OrderedDict[Text, Any]
        return OrderedDict(self.pretty_tuples())

    def pretty_lines(self, pair_sep=u": ", line_start=u"  "):
        # type: (Text, Text) -> List[Text]
        lines = []
        for key, value in self.pretty_tuples():
            line = u"{0}{1}{2}".format(key, pair_sep, value)
            lines.append(line)
        return lines

    def pretty_text(
            self, line_start=u"", line_sep=u"\n", line_end=u"", pair_sep=u": ",
    ):
        # type: (Text, Text, Text, Text) -> Text
        lines = self.pretty_lines(pair_sep=pair_sep, line_start=line_start)
        text = line_sep.join([
            "{0}{1}{2}".format(line_start, line, line_end)
            for line in lines
        ])
        return text
