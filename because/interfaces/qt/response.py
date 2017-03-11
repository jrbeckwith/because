import logging
import json
import textwrap


# TODO: make a qreply -> Response conversion
def unpack_qnetworkreply(qreply):
    url = qreply.url().toString()
    error = qreply.error()
    header_pairs = [
        # (pair[0].constData(), pair[1].constData())
        (pair[0].data(), pair[1].data())
        for pair in qreply.rawHeaderPairs()
    ]
    return {
        "url": url,
        "error": error,
        "headers": header_pairs,
    }


# TODO: error should not be on this, this should only encode when we actually
# got a response. means a different callback handles the errors vs the
# responses
class Response(object):
    def __init__(self, status, headers, body, error=None, redirect=None):
        self.status = status
        self.headers = headers
        self.body = body
        self.error = error
        self.redirect = redirect

    def pretty(self, indent="  "):
        lines = []
        lines.append(
            "{0}status: {1}".format(indent, self.status),
        )
        if self.error:
            lines.append(
                "{0}error: {1}".format(indent, self.error),
            )
        if self.redirect:
            lines.append(
                "{0}redirect: {1}".format(indent, self.redirect),
            )
        if self.headers:
            lines.append(
                "{0}headers:".format(indent),
            )
            for header_name, header_value in self.headers:
                lines.append(
                    "{0}{1}: {2!r}".format(indent * 2, header_name, header_value)
                )
        if self.body:
            lines.extend([
                "{0}body:".format(indent),
                "{0}{1!r}".format(indent * 2, self.body),
            ])
        return "\n".join(lines)

    def _pretty_lines(self, show_body=True):
        blob = self._pretty(show_body=show_body)
        return [blob]
        # return blob.split("\n")

        # lines = []
        # lines.append("HTTP status: {}".format(response.status))
        # lines.append("Headers:")
        # for header in response.headers:
        #     lines.append("* {0}={1}".format(header[0], header[1]))
        # lines.append("")
        # lines.append("Body size: {} bytes".format(len(body)))

    def _pretty(self, show_body=True):
        """Pretty print the response for debug

        This will go away, maybe in favor of something cleaner, maybe nothing
        """
        if show_body:
            body_raw = "".join(self.body)
            body_repr = body_raw
            try:
                body_dict = json.loads(body_raw)
                body_repr = json.dumps(body_dict, indent=4)
            except ValueError as error:
                if error.message != "No JSON object could be decoded":
                    raise
                body_repr = body_raw

            # KLUDGE: restore iterator for others
            self.body = iter([body_raw])

        else:
            body_repr = "(BODY SUPPRESSED)"

        formatted_headers = "\n".join([
            "  * {0}={1}".format(key, value)
            for key, value in self.headers
        ])
        formatted_response = textwrap.dedent("""
            Error: {error}
            Status: {status!r}
            Redirect: {redirect}
            Headers: {headers}
            Body: {body}
        """).strip().format(
            error=self.error,
            redirect=self.redirect,
            status=self.status,
            body=body_repr,
            headers=formatted_headers,
        )
        return formatted_response

    def as_json(self):
        # Exhaust response body iterator and store in memory
        # TODO: large bodies could be an issue
        body = "".join(self.body)

        # TODO: ugh. preserve body for other uses
        self.body = [body]

        # Try to parse response body as JSON
        data = None
        try:
            data = json.loads(body)
        except ValueError:
            logging.exception("JSON parse error")

        return data
