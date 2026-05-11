import argparse
import json
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(__file__))

from client import HTTPClient, HTTPResponse

_COLOR_GREEN  = "\033[92m"
_COLOR_YELLOW = "\033[93m"
_COLOR_RED    = "\033[91m"
_COLOR_RESET  = "\033[0m"

def _status_color(code: int) -> str:
    if code < 300:
        return _COLOR_GREEN
    if code < 400:
        return _COLOR_YELLOW
    return _COLOR_RED


def _print_response(resp: HTTPResponse) -> None:
    color = _status_color(resp.status_code)
    print(f"\n  {color}HTTP/1.1 {resp.status_code} {resp.status_text}{_COLOR_RESET}")

    for name, value in resp.headers.items():
        print(f"  {name}: {value}")
    for cookie in resp.set_cookies:
        print(f"  Set-Cookie: {cookie}")

    if resp.body:
        print()
        ct = resp.headers.get("content-type", "")
        if "application/json" in ct:
            try:
                pretty = json.dumps(resp.json(), indent=2, ensure_ascii=False)
                for line in pretty.splitlines():
                    print(f"  {line}")
            except ValueError:
                print(f"  {resp.text()}")
        elif "text/" in ct:
            for line in textwrap.wrap(resp.text(), width=80) or [resp.text()]:
                print(f"  {line}")
        else:
            print(f"  <binario, {len(resp.body)} bytes>")
    print()



def _run_once(method, url, headers, body, api_key):
    with HTTPClient(api_key=api_key) as c:
        try:
            resp = c.request(method, url, headers=headers or None, body=body or None)
            _print_response(resp)
        except Exception as e:
            print(f"\n  [ERROR] {e}\n")
            sys.exit(1)


def _command_line_interface(api_key):
    print("=" * 60)
    print(" USJ HTTP Client - Command Line Interface")
    print(" Write 'exit' or press Ctrl-C to leave")
    print("=" * 60)

    client = HTTPClient(api_key=api_key)

    try:
        while True:
            try:
                line = input("\n Method + URL > ").strip()
            except(EOFError, KeyboardInterrupt):
                    print("\n\n Bye!")
                    break
            
            if line.lower() in ("exit", "quit", "q", "logout"):
                print(" Bye!")
                break
        
            parts = line.split(None, 1)
            if len(parts) != 2:
                print("Expected Format: Method + URL (Exp: GET http://localhost:8080/bunnies)")
                continue

            method, url = parts[0].upper(), parts[1]

            headers: dict[str, str] = {}
            print("Extra Headers (Name: Value), Press ENTER to Skip:")
            while True:
                try:
                    h = input("     header > ").strip()
                except EOFError:
                    break
                if not h:
                    break
                if ":" in h:
                    name, _, value = h.partition(":")
                    headers[name.strip()] = value.strip()

            body = b""
            if method in ("POST", "PUT", "PATCH"):
                print(" Body (Press ENTER to Skip)")
                lines: list[str] = []
                try:
                    while True:
                        bl = input("     body >")
                        if not bl:
                            break
                        lines.append(bl)
                except EOFError:
                    pass

                if lines:
                    raw_body = "\n".join(lines)
                    body = raw_body.encode("utf-8")
                    if "content-type" not in {k.lower() for k in headers}:
                        try:
                            json.loads(raw_body)
                            headers["Content-Type"] = "application/json"
                        except ValueError:
                            pass

            try:
                resp = client.request(method, url, headers=headers or None, body=body or None,)
                _print_response(resp)
            except Exception as e:
                print(f"\n [ERROR] {e}\n")

    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description="USJ HTTP/1.1 Client", formatter_class=argparse.RawTextHelpFormatter,)
    parser.add_argument("method", nargs="?", default="", help="Method HTTP: GET, POST, PUT, DELETE, HEAD")
    parser.add_argument("url", nargs="?", default="", help="URL Destiny: http//localhost:8080/bunnies")
    parser.add_argument("-H", "--header", action="append", default=[], metavar="Name:Value", help="Extra Header")
    parser.add_argument("-b", "--body", default="", help="Body of the Request")
    parser.add_argument("--api-key", default=None, help="X-API-Key Value")
    args = parser.parse_args()

    extra_headers: dict[str, str] = {}
    for h in args.header:
        if ":" in h:
            name, _, value = h.partition(":")
            extra_headers[name.strip()] = value.strip()

    body = args.body.encode("utf-8") if args.body else b""

    if args.method and args.url:
        _run_once(args.method.upper(), args.url, extra_headers, body, args.api_key)
    else:
        _command_line_interface(args.api_key)



if __name__ == "__main__":
    main()