import json
from http_parser import HTTPRequest
from http_response import HTTPResponse

_bunnies = {}
_next_id = 1

REQUIRED_FIELDS = {"name", "breed", "age"}


def _validate(data: dict) -> bool:
    return REQUIRED_FIELDS.issubset(data.keys())


def get_all(request: HTTPRequest) -> HTTPResponse:
    return HTTPResponse.ok(list(_bunnies.values()))


def get_one(request: HTTPRequest, id: str) -> HTTPResponse:
    bunny = _bunnies.get(int(id))
    if not bunny:
        return HTTPResponse.not_found(f"bunny {id} not found")
    return HTTPResponse.ok(bunny)


def create(request: HTTPRequest) -> HTTPResponse:
    global _next_id
    try:
        data = request.json()
    except Exception:
        return HTTPResponse.bad_request("Body must be valid JSON")

    if not _validate(data):
        return HTTPResponse.bad_request(f"Missing fields. Required: {REQUIRED_FIELDS}")

    bunny = {"id": _next_id, **data}
    _bunnies[_next_id] = bunny
    _next_id += 1
    return HTTPResponse.created(bunny)


def update(request: HTTPRequest, id: str) -> HTTPResponse:
    bunny_id = int(id)
    if bunny_id not in _bunnies:
        return HTTPResponse.not_found(f"bunny {id} not found")

    try:
        data = request.json()
    except Exception:
        return HTTPResponse.bad_request("Body must be valid JSON")

    _bunnies[bunny_id] = {"id": bunny_id, **data}
    return HTTPResponse.ok(_bunnies[bunny_id])


def delete(request: HTTPRequest, id: str) -> HTTPResponse:
    bunny_id = int(id)
    if bunny_id not in _bunnies:
        return HTTPResponse.not_found(f"bunny {id} not found")

    del _bunnies[bunny_id]
    return HTTPResponse.no_content()