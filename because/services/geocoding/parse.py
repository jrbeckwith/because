from because.response import parse_json
from because.errors import ParseError
from . candidate import Candidate


def _check_for_errors(data, response):
    """Check data for keys known to indicate errors from this endpoint.
    """
    # TODO: what regularity is there across endpoints in these?
    error_code = data.get("errorCode")
    error_message = data.get("errorMessage")
    if error_code or error_message:
        raise ParseError(
            "JSON response body contained error {0}: {1}"
            .format(error_code, error_message),
            response=response
        )


_FIELD_MAPPING = {
    "candidatePlace": "address",
    "candidateSource": "source",
}


def _map_field(key):
    """Translate a name in a geocoding result to a Candidate attribute name.
    """
    return _FIELD_MAPPING.get(key, key)


def parse_forward_geocodes(response):
    """Parse a forward geocoding response.
    """
    data = parse_json(response, required_keys=["geocodePoints"])
    _check_for_errors(data, response)
    records = data.get("geocodePoints")
    records = [
        {
            _map_field(key): value
            for key, value in record.items()
        }
        for record in records
    ]
    candidates = [
        Candidate(**record)
        for record in records
    ]
    return candidates


def parse_reverse_geocodes(response):
    """Parse a reverse geocoding response.
    """
    data = parse_json(response, required_keys=["geocodePoints"])
    _check_for_errors(data, response)
    records = data.get("geocodePoints")
    records = [
        {
            _map_field(key): value
            for key, value in record.items()
        }
        for record in records
    ]
    candidates = [
        Candidate(**record)
        for record in records
    ]
    return candidates
