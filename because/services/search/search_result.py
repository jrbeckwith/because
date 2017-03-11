from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from collections import OrderedDict
from because.errors import ParseError
from because.reprs import ReprMixin
from because.pretty import PrettyMixin


class SearchResult(ReprMixin, PrettyMixin):
    def __init__(
            self,
            title,
            url,
            role=None,
            description="",
            content="",
            category=None,
            author=None,
    ):
        self.title = title
        self.role = role
        self.description = description
        self.category = category
        self.url = url
        self.author = author

    def repr_data(self):
        return OrderedDict([
            ("title", self.title),
            ("category", self.category),
            ("role", self.role),
            ("url", self.url),
            ("description", self.description),
        ])



def _xml_text(el):
    return el.firstChild.nodeValue if el and el.firstChild else None


def parse_opensearch_xml(data):
    doc = parseString(data)
    entries = doc.getElementsByTagName("entry")

    # I like comprehensions, but this will give better tracebacks
    results = []
    for entry in entries:
        try:
            data = parse_opensearch_xml_entry(entry)
        # raise a predictable exception type wrapping the xml exception
        except ExpatError as error:
            raise ParseError(
                "error parsing opensearch XML",
                error=error,
            )
        result = SearchResult(**data)
        results.append(result)
    return results


def parse_opensearch_xml_entry(entry):
    el_title = entry.getElementsByTagName("title")[0]
    el_link = entry.getElementsByTagName("link")[0]
    el_category = entry.getElementsByTagName("category")[0]
    el_author = entry.getElementsByTagName("author")[0]
    el_name = el_author.getElementsByTagName("name")[0]
    el_content = entry.getElementsByTagName("content")[0]

    return {
        "title": _xml_text(el_title),
        "url": el_link.getAttribute("href"),
        "category": el_category.getAttribute("term"),
        "author": _xml_text(el_name),
        "content": _xml_text(el_content),
    }
