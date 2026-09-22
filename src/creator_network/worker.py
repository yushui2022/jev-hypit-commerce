import threading
import uuid

from .decision import ProviderError
from .pipeline import MatchingPipeline
from .rendering import render


class Worker:
    def __init__(self, settings, store, pipeline=None):
        self.settings = settings
        self.store = store
        self.pipeline = pipeline or MatchingPipeline(settings, store)
        self.owner = uuid.uuid4().hex
        self.stop = threading.Event()

    def once(self):
        job = self.store.claim(self.owner)
        if not job:
            return False
        done = threading.Event()

        def heartbeat():
            while not done.wait(20):
                if not self.store.heartbeat(job["id"], self.owner):
                    return

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            if job["kind"] == "match":
                result = self.pipeline.run(job["payload"])
            elif job["kind"] == "render":
                result = render(self.settings, job)
            else:
                raise ValueError("Unknown job kind")
            self.store.finish(job["id"], self.owner, result=result)
        except Exception as e:  # noqa: BLE001 — task boundary must persist any job failure
            # Provider payloads, credentials and local paths never enter public error fields.
            error = (
                str(e)
                if isinstance(e, ProviderError)
                else "job_failed:" + type(e).__name__
            )
            self.store.finish(job["id"], self.owner, error=error)
        finally:
            done.set()
            thread.join(timeout=1)
        return True

    def run(self):
        while not self.stop.is_set():
            if not self.once():
                self.stop.wait(0.4)
