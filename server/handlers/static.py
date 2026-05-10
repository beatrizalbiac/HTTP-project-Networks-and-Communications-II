import os
from http_parser import HTTPRequest
from http_response import HTTPResponse
from config import STATIC_DIR

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css",
    ".js":   "application/javascript",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".ico":  "image/x-icon",
}


def serve_static(request: HTTPRequest, filename: str = "index.html") -> HTTPResponse:
    filepath = os.path.join(STATIC_DIR, filename)

    if not os.path.isfile(filepath):
        return HTTPResponse.not_found(f"File {filename} not found")

    ext = os.path.splitext(filename)[1]
    content_type = MIME_TYPES.get(ext, "application/octet-stream")

    with open(filepath, "rb") as f:
        content = f.read()

    return HTTPResponse.ok(body=content, content_type=content_type)