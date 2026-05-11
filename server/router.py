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
        meth_allowed: list[str] = []

        for method, pattern, param_names, handler in self._routes:
            match = pattern.match(request.path)
            if not match:
                continue

            meth_allowed.append(method)
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

        if meth_allowed:
            return HTTPResponse.method_not_allowed(meth_allowed)
        
        return HTTPResponse.not_found()