"""
HTTP/1.1 Client


"""
from __future__ import annotations

import socket
import ssl
import time
import urllib.parse
import json
from dataclasses import dataclass, field
from typing import Optional

_DEFAULT_HEADERS = {
    "User-Agent": "USJ-HTTPClient/1.0",
    "Accept": "*/*",
    "Accept-Encoding": "identity",
}

class SocketReader:
    _CHUNK = 4096

    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._buf = b""

    def _fill(self) -> bool:
        data = self._sock.recv(self._CHUNK)
        if not data:
            return False
        self._buf += data
        return True
    
    def read_line(self) -> bytes:
        while b"\r\n" not in self._buf:
            if not self._fill():
                line = self._buf
                self._buf = b""
                return line
        index = self._buf.index(b"\r\n")
        line = self._buf[: index + 2]
        self._buf = self._buf[index + 2 :]
        return line
    
    def read_exactly(self, n: int) -> bytes:
        while len(self._buf) < n:
            if not self._fill():
                break
        data = self._buf[:n]
        self._buf = self._buf[n:]
        return data
    
    def read_chunked(self) -> bytes:
        pieces: list[bytes] = []
        while True:
            size_line = self.read_line().split(b";")[0].strip()
            if not size_line:
                continue
            chunk_size = int(size_line, 16)
            if chunk_size == 0:
                self.read_line()
                break
            pieces.append(self.read_exactly(chunk_size))
            self.read_line()
        return b"".join(pieces)
    

@dataclass
class HTTPResponse:
    status_code: int
    status_text: str
    headers: dict[str, str]
    body: bytes
    set_cookies: list[str]

    def json(self) -> object:
        return json.loads(self.body.decode("utf-8"))
    
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")
    
    def __repr__(self) -> str:
        return f"<HTTPResponse {self.status_code} {self.status_text}>"
    
def _parse_response(reader: SocketReader) -> Optional[HTTPResponse]:
    status_line_bytes = reader.read_line()
    if not status_line_bytes:
        return None
    try:
        decoded = status_line_bytes.decode("utf-8").strip()
        _version, status_str, *rest = decoded.split(" ", 2)
        status_code = int(status_str)
        status_text = rest[0] if rest else ""
    except (ValueError, IndexError):
        return None
    
    headers: dict[str, str] = {}
    set_cookies: list[str] = []

    while True:
        raw = reader.read_line().strip()
        if not raw:
            break
        if b":" not in raw:
            continue
        name, _, value = raw.decode("utf-8", errors="replace").partition(":")
        key = name.strip().lower()
        if key == "set-cookie":
            set_cookies.append(value.strip())
        else:
            headers[key] = value.strip()

    body = b""
    transfencod_flag = headers.get("transfer-encoding", "").lower()

    if transfencod_flag == "chunked":
        body = reader.read_chunked()
    elif "content-length" in headers:
        length = int(headers["content-length"])
        if length > 0:
            body = reader.read_exactly(length)
    elif status_code not in (204, 304) and headers.get("connection", "") == "close":
        pieces: list[bytes] = []
        while chunk := reader.read_exactly(4096):
            pieces.append(chunk)
        body = b"".join(pieces)

    return HTTPResponse(status_code=status_code, status_text=status_text, headers=headers, body=body, set_cookies=set_cookies)


@dataclass
class _Cookie:
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: Optional[float] = None

    def is_expired(self) -> bool:
        return self.expires is not None and time.time() > self.expires
    
    def matches(self, domain: str, path: str) -> bool:
        domain_state = domain == self.domain or domain.endswith("." + self.domain)
        path_state = path == self.path or path.startswith(self.path.rstrip("/") + "/")
        return domain_state and path_state and not self.is_expired()
    
class CookieJar:
    def __init__(self) -> None:
        self._cookies: dict[tuple[str, str], _Cookie] = {}

    def ingest(self, set_cookie_headers: list[str], domain: str) -> None:
        for header in set_cookie_headers:
            parts = [p.strip() for p in header.split(";")]
            if not parts or "=" not in parts[0]:
                continue

            name, _, value = parts[0].partition("=")

            attrs: dict[str, str] = {}
            for attr_aux in parts[1:]:
                if "=" in attr_aux:
                    cky, _, val = attr_aux.partition("=")
                    attrs[cky.strip().lower()] = val.strip()
                else:
                    attrs[attr_aux.strip().lower()] = ""
            
            expires = None
            if "max-age" in attrs:
                try:
                    expires = time.time() + float(attrs["max-age"])
                except ValueError:
                    pass
            
            cookie = _Cookie(name=name.strip(), value=value.strip(), domain=attrs.get("domain", domain), path=attrs.get("path", "/"), expires=expires)
            self._cookies[(cookie.domain, cookie.name)] = cookie

    def get_header(self, domain: str, path: str) -> Optional[str]:
        matching = [c for c in self._cookies.values() if c.matches(domain, path)]
        if not matching:
            return None
        return "; ".join(f"{c.name}={c.value}" for c in matching)
    

@dataclass
class _Connection:
    host: str
    port: str
    sock: socket.socket
    reader: SocketReader
    is_tls: bool = False

    def send(self, data: bytes) -> None:
        self.sock.sendall(data)

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


def _build_request(method: str, path: str, headers: dict[str, str], body: bytes) -> bytes:
    lines = [f"{method} {path} HTTP/1.1\r\n"]
    for name, value in headers.items():
        lines.append(f"{name}: {value}\r\n")
    lines.append("\r\n")
    return "".join(lines).encode("utf-8") + body


class HTTPClient:
    def __init__(self, *, api_key: Optional[str] = None, timeout: int = 30,) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._jar = CookieJar()
        self._conn: Optional[_Connection] = None

    def _get_connection(self, host: str, port: int, *, use_tls: bool) -> _Connection:
        if(self._conn and self._conn.host == host and self._conn.port == port and self._conn.is_tls == use_tls):
            return self._conn
        
        if self._conn:
            self._conn.close()

        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(self._timeout)
        raw_sock.connect((host, port))

        if use_tls:
            context = ssl.create_default_context()
            sock: socket.socket = context.wrap_socket(raw_sock, server_hostname=host)
        else:
            sock = raw_sock

        self._conn = _Connection(host=host, port=port, sock=sock, reader=SocketReader(sock), is_tls=use_tls)
        return self._conn

    def request(self, method: str, url: str, *, headers: Optional[dict[str, str]] = None, body: Optional[bytes] = None, json_body: object = None) -> HTTPResponse:
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers = {"Content-Type": "application/json", **(headers or {})}

        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme.lower()
        host = parsed.hostname or ""
        port = parsed.port or (443 if scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        
        conn = self._get_connection(host, port, use_tls=(scheme == "https"))

        req_headers: dict[str, str] = {**_DEFAULT_HEADERS}

        req_headers["Host"] = f"{host}:{port}" if port not in (80, 443) else host
        req_headers["Connection"] = "keep-alive"

        if self._api_key:
            req_headers["X-API-Key"] = self._api_key

        cookie_val = self._jar.get_header(host, path)
        if cookie_val:
            req_headers["Cookie"] = cookie_val

        if body:
            req_headers["Content-Length"] = str(len(body))

        if headers:
            req_headers.update(headers)

        raw = _build_request(method.upper(), path, req_headers, body or b"")

        try:
            conn.send(raw)
        except OSError:
            conn.close()
            self._conn = None
            conn = self._get_connection(host, port, use_tls=(scheme == "https"))
            conn.send(raw)

        resp = _parse_response(conn.reader)
        if resp is None:
            conn.close()
            self._conn = None
            conn = self._get_connection(host, port, use_tls=(scheme == "https"))
            conn.send(raw)
            resp = _parse_response(conn.reader)
            if resp is None:
                raise ConnectionError("The server closed the connection without responding")
            
        if resp.set_cookies:
            self._jar.ingest(resp.set_cookies, host)

        if resp.headers.get("connection", "").lower() == "close":
            conn.close()
            self._conn = None
        else:
            self._conn = conn
        
        return resp
    
    def get(self, url: str, **kw) -> HTTPResponse:
        return self.request("GET", url, **kw)
    
    def post(self, url: str, **kw) -> HTTPResponse:
        return self.request("POST", url, **kw)
    
    def put(self, url: str, **kw) -> HTTPResponse:
        return self.request("PUT", url, **kw)
    
    def delete(self, url: str, **kw) -> HTTPResponse:
        return self.request("DELETE", url, **kw)
    
    def head(self, url: str, **kw) -> HTTPResponse:
        return self.request("HEAD", url, **kw)
    
    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self) -> "HTTPClient":
        return self
    
    def __exit__(self, *_) -> None:
        self.close()