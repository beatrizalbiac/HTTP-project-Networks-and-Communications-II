from http_parser import HTTPRequest
from http_response import HTTPResponse
from config import API_KEY, API_KEY_HEADER
from logger import logger

PUBLIC_PATHS = ["/", "/index.html", "/adoption.html"]


def api_key_middleware(request: HTTPRequest):
    if request.path in PUBLIC_PATHS:
        return None

    key = request.header(API_KEY_HEADER)
    if key != API_KEY:
        logger.warning(f"Unauthorized request to {request.path}")
        return HTTPResponse.unauthorized()

    return None


def logging_middleware(request: HTTPRequest):
    return None