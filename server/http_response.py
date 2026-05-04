import json as _json

# the more common ones
STATUS_TEXTS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}


class HTTPResponse:
    def __init__(self, status: int, body=None, content_type: str = "application/json", headers: dict = None):
        self.status = status
        self.content_type = content_type
        self.extra_headers = headers or {}
        self._cookies = []

        if body is None:
            self.body = b""
        elif isinstance(body, (dict, list)):
            self.body = _json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            self.body = body.encode("utf-8")
        else:
            self.body = body  # they're already bytes

    def set_cookie(self, name: str, value: str, max_age: int = None, path: str = "/"):
        cookie = f"{name}={value}; Path={path}"
        if max_age is not None:
            cookie += f"; Max-Age={max_age}"
        self._cookies.append(cookie)

    def to_bytes(self) -> bytes:
        reason = STATUS_TEXTS.get(self.status, "Unknown")
        lines = [f"HTTP/1.1 {self.status} {reason}"]

        if self.body:
            lines.append(f"Content-Type: {self.content_type}")
        lines.append(f"Content-Length: {len(self.body)}")
        lines.append("Connection: keep-alive")

        for k, v in self.extra_headers.items():
            lines.append(f"{k}: {v}")

        for cookie in self._cookies:
            lines.append(f"Set-Cookie: {cookie}")

        header_str = "\r\n".join(lines) + "\r\n\r\n"
        return header_str.encode("utf-8") + self.body

    # just for the ones that the assingment requires
    @classmethod
    def ok(cls, body=None, **kwargs):
        return cls(200, body, **kwargs)

    @classmethod
    def created(cls, body=None, **kwargs):
        return cls(201, body, **kwargs)

    @classmethod
    def no_content(cls):
        return cls(204)

    @classmethod
    def not_found(cls, message="Not found"):
        return cls(404, {"error": message})

    @classmethod
    def bad_request(cls, message="Bad request"):
        return cls(400, {"error": message})

    @classmethod
    def method_not_allowed(cls):
        return cls(405, {"error": "Method not allowed"})

    @classmethod
    def unauthorized(cls):
        return cls(401, {"error": "Unauthorized"})