import argparse
import json

from .config import Settings
from .store import Store


def main():
    p = argparse.ArgumentParser(description="Jev Creator Network")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--showcase", action="store_true")
    s = sub.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8890)
    s.add_argument("--external-worker", action="store_true")
    sub.add_parser("worker")
    sub.add_parser("evaluate")
    args = p.parse_args()
    settings = Settings()
    store = Store(settings.database)
    if settings.retrieval not in ("lexical", "hybrid"):
        p.error("CREATOR_RETRIEVAL must be lexical or hybrid")
    if args.command == "seed":
        from .seed import seed

        print(json.dumps(seed(settings, store, args.showcase)))
    elif args.command == "worker":
        from .worker import Worker

        Worker(settings, store).run()
    elif args.command == "evaluate":
        from .evaluation import evaluate

        print(json.dumps(evaluate(settings), indent=2))
    else:
        if (
            args.host not in ("127.0.0.1", "localhost", "::1")
            and not settings.api_token
        ):
            p.error("Set CREATOR_API_TOKEN before binding beyond localhost")
        import uvicorn

        from .api import create_app

        settings.worker_enabled = not args.external_worker
        uvicorn.run(create_app(settings), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
