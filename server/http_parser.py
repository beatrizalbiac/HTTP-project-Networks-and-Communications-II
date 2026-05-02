# REVISAR

import json

class HTTPRequest:
    def __init__(self):
        self.method = ""
        self.path = ""
        self.version = ""
        self.headers = {}
        self.body = b""
        self.query_params = {}

    def json(self):
        return json.loads(self.body.decode("utf-8"))

    def header(self, name: str):
        return self.headers.get(name.lower())


class HTTPParser:
    @staticmethod
    def parse(raw: bytes):
        try:
            header_section, _, body = raw.partition(b"\r\n\r\n")
            lines = header_section.split(b"\r\n")

            # Request line
            request_line = lines[0].decode("utf-8")
            parts = request_line.split(" ")
            if len(parts) != 3:
                return None

            method, full_path, version = parts[0], parts[1], parts[2]

            # Path y query params
            path, query_params = HTTPParser._parse_path(full_path)

            # Headers
            headers = {}
            for line in lines[1:]:
                if b":" in line:
                    key, _, value = line.partition(b":")
                    headers[key.decode().strip().lower()] = value.decode().strip()

            # Body
            content_length = int(headers.get("content-length", 0))

            req = HTTPRequest()
            req.method = method.upper()
            req.path = path
            req.version = version
            req.headers = headers
            req.body = body[:content_length]
            req.query_params = query_params
            return req

        except Exception:
            return None

    @staticmethod
    def _parse_path(full_path: str):
        if "?" in full_path:
            path, qs = full_path.split("?", 1)
            params = {}
            for pair in qs.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v
            return path, params
        return full_path, {}