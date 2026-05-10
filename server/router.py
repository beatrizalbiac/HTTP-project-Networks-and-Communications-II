import re
from http_parser import HTTPRequest
from http_response import HTTPResponse
from logger import logger


class Router:
    def __init__(self):
        self._routes = []
        self._middlewares = []

    def add_middleware(self, fn):
        self._middlewares.append(fn)

    def add(self, method: str, path: str, handler):
        param_names = re.findall(r":(\w+)", path)
        pattern = re.sub(r":(\w+)", r"([^/]+)", path)
        pattern = f"^{pattern}$"
        self._routes.append((method.upper(), re.compile(pattern), param_names, handler))

    def dispatch(self, request: HTTPRequest) -> HTTPResponse:
        path_matched = False

        for method, pattern, param_names, handler in self._routes:
            match = pattern.match(request.path)
            if match:
                path_matched = True
                if request.method != method:
                    continue

                params = dict(zip(param_names, match.groups()))

                for middleware in self._middlewares:
                    result = middleware(request)
                    if isinstance(result, HTTPResponse):
                        return result

                try:
                    return handler(request, **params)
                except Exception as e:
                    logger.error(f"Handler error: {e}", exc_info=True)
                    return HTTPResponse(500, {"error": "Internal server error"})

        if path_matched:
            return HTTPResponse.method_not_allowed()
        return HTTPResponse.not_found()