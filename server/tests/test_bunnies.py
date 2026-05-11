import pytest
import socket
import json
import time
import threading

from router import Router
from tcp_server import TCPServer
from middleware import logging_middleware, api_key_middleware
from handlers import bunny

TEST_PORT = 8099


def build_test_router():
    router = Router()
    router.add_middleware(logging_middleware)
    router.add_middleware(api_key_middleware)
    router.add("GET",    "/bunnies",      bunny.get_all)
    router.add("GET",    "/bunnies/:id",  bunny.get_one)
    router.add("POST",   "/bunnies",      bunny.create)
    router.add("PUT",    "/bunnies/:id",  bunny.update)
    router.add("DELETE", "/bunnies/:id",  bunny.delete)
    return router


@pytest.fixture(scope="module", autouse=True)
def start_server():
    bunny._bunnies.clear()
    bunny._next_id = 1

    router = build_test_router()
    server = TCPServer(router, "127.0.0.1", TEST_PORT)
    t = threading.Thread(target=server.start, daemon=True)
    t.start()
    time.sleep(0.3)
    yield


def send_raw(method, path, body=None, api_key="1234"):
    payload = json.dumps(body).encode() if body else b""
    headers = {
        "Host": f"127.0.0.1:{TEST_PORT}",
        "Content-Type": "application/json",
        "Content-Length": str(len(payload)),
        "Connection": "close",
    }
    if api_key:
        headers["x-api-key"] = api_key
    header_str = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
    raw = f"{method} {path} HTTP/1.1\r\n{header_str}\r\n\r\n".encode() + payload

    with socket.create_connection(("127.0.0.1", TEST_PORT)) as s:
        s.sendall(raw)
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk

    status_code = int(response.split(b"\r\n")[0].decode().split(" ")[1])
    _, _, response_body = response.partition(b"\r\n\r\n")
    parsed = json.loads(response_body) if response_body.strip() else None
    return status_code, parsed


def test_get_empty():
    bunny._bunnies.clear()
    bunny._next_id = 1
    status, body = send_raw("GET", "/bunnies")
    assert status == 200
    assert body == []


def test_create_bunny():
    status, body = send_raw("POST", "/bunnies", {"name": "Cookie", "breed": "Cinnamon", "age": 2})
    assert status == 201
    assert body["name"] == "Cookie"
    assert "id" in body


def test_get_all_has_one():
    status, body = send_raw("GET", "/bunnies")
    assert status == 200
    assert len(body) == 1


def test_get_one():
    status, body = send_raw("GET", "/bunnies/1")
    assert status == 200
    assert body["id"] == 1


def test_get_nonexistent():
    status, _ = send_raw("GET", "/bunnies/999")
    assert status == 404


def test_update_bunny():
    status, body = send_raw("PUT", "/bunnies/1", {"name": "Cookie", "breed": "Cinnamon", "age": 5})
    assert status == 200
    assert body["age"] == 5


def test_delete_bunny():
    status, _ = send_raw("DELETE", "/bunnies/1")
    assert status == 204


def test_delete_nonexistent():
    status, _ = send_raw("DELETE", "/bunnies/10")
    assert status == 404


def test_bad_json():
    with socket.create_connection(("127.0.0.1", TEST_PORT)) as s:
        raw = b"POST /bunnies HTTP/1.1\r\nHost: localhost\r\nx-api-key: 1234\r\nContent-Type: application/json\r\nContent-Length: 5\r\nConnection: close\r\n\r\n{bad}"
        s.sendall(raw)
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
    status_code = int(response.split(b"\r\n")[0].decode().split(" ")[1])
    assert status_code == 400


def test_method_not_allowed():
    status, _ = send_raw("PATCH", "/bunnies")
    assert status == 405


def test_unauthorized_no_key():
    status, _ = send_raw("GET", "/bunnies", api_key=None)
    assert status == 401


def test_keep_alive():
    sock = socket.create_connection(("127.0.0.1", TEST_PORT))

    def make_raw(method, path):
        headers = {
            "Host": f"127.0.0.1:{TEST_PORT}",
            "x-api-key": "1234",
            "Content-Length": "0",
            "Connection": "keep-alive",
        }
        header_str = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
        return f"{method} {path} HTTP/1.1\r\n{header_str}\r\n\r\n".encode()

    try:
        sock.sendall(make_raw("GET", "/bunnies"))
        resp1 = b""
        while b"\r\n\r\n" not in resp1:
            resp1 += sock.recv(4096)

        sock.sendall(make_raw("GET", "/bunnies"))
        resp2 = b""
        while b"\r\n\r\n" not in resp2:
            resp2 += sock.recv(4096)

        status1 = int(resp1.split(b"\r\n")[0].decode().split(" ")[1])
        status2 = int(resp2.split(b"\r\n")[0].decode().split(" ")[1])
        assert status1 == 200
        assert status2 == 200
    finally:
        sock.close()


def test_content_length_present():
    with socket.create_connection(("127.0.0.1", TEST_PORT)) as s:
        raw = b"GET /bunnies HTTP/1.1\r\nHost: localhost\r\nx-api-key: 1234\r\nConnection: close\r\n\r\n"
        s.sendall(raw)
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
    headers_part = response.split(b"\r\n\r\n")[0].decode().lower()
    assert "content-length" in headers_part or "transfer-encoding: chunked" in headers_part