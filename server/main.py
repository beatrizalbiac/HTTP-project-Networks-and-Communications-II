from router import Router
from handlers import bunny
from tcp_server import TCPServer
from middleware import api_key_middleware, logging_middleware
from handlers import static
from config import HOST, PORT


def build_router() -> Router:
    router = Router()

    router.add_middleware(logging_middleware)
    router.add_middleware(api_key_middleware)

    router.add("GET", "/",              lambda req: static.serve_static(req, "index.html"))
    router.add("GET", "/index.html",    lambda req: static.serve_static(req, "index.html"))
    router.add("GET", "/adoption.html", lambda req: static.serve_static(req, "adoption.html"))

    router.add("GET",    "/bunnies",      bunny.get_all)
    router.add("GET",    "/bunnies/:id",  bunny.get_one)
    router.add("POST",   "/bunnies",      bunny.create)
    router.add("PUT",    "/bunnies/:id",  bunny.update)
    router.add("DELETE", "/bunnies/:id",  bunny.delete)
    router.add("HEAD", "/bunnies",     bunny.get_all)
    router.add("HEAD", "/bunnies/:id", bunny.get_one)

    return router


if __name__ == "__main__":
    router = build_router()
    server = TCPServer(router, HOST, PORT)
    server.start()