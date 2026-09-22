import time

from .decision import JevSelector
from .retrieval import bm25, document, fuse


class MatchingPipeline:
    def __init__(self, settings, store, selector=None, semantic=None):
        self.settings = settings
        self.store = store
        self.selector = selector or JevSelector(settings.jev_key)
        self.semantic = semantic

    def run(self, request):
        start = time.perf_counter()
        p = self.store.item(request["product_id"])
        if p["kind"] != "product" or not p.get("active", True):
            raise ValueError("Product is unavailable")
        market = request.get("market") or p["market"]
        language = request.get("language") or p["language"]
        eligible = [
            x
            for x in self.store.items("creator")
            if x["active"] and x["market"] == market and x["language"] == language
        ]
        query = document(p)
        lex = bm25(query, eligible)
        retrieval = "bm25"
        if self.settings.retrieval == "hybrid":
            if self.semantic is None:
                from .semantic import SemanticIndex

                self.semantic = SemanticIndex(self.settings)
            ranking = fuse(lex, self.semantic.rank(query, eligible))
            retrieval = "bm25+dense+rrf"
        else:
            ranking = lex
        candidates = ranking[: request["top_k"]]
        retrieved = time.perf_counter()
        if not candidates:
            decision = {
                "creator_id": None,
                "confidence": None,
                "provider": "none",
                "note": "No eligible matching candidates",
            }
        elif request["engine"] == "jev":
            decision = self.selector.choose(p, candidates)
        else:
            decision = {
                "creator_id": candidates[0]["creator"]["id"],
                "confidence": None,
                "provider": "baseline",
                "mechanism": "retrieval_rank",
                "note": "Retrieval baseline; not a Jev model decision.",
            }
        confident = (
            decision["provider"] == "jev"
            and (decision["confidence"] or 0) >= self.settings.confidence_threshold
        )
        selected = decision["creator_id"]
        return {
            "product": p,
            "candidates": candidates,
            "decision": decision,
            "review": {"status": "pending", "creator_id": None},
            "review_recommended": not confident,
            "trace": {
                "eligible_count": len(eligible),
                "candidate_count": len(candidates),
                "retrieval": retrieval,
                "retrieval_ms": round((retrieved - start) * 1000, 2),
                "total_ms": round((time.perf_counter() - start) * 1000, 2),
                "market": market,
                "language": language,
                "threshold": self.settings.confidence_threshold,
            },
            "selected_creator": next(
                (r["creator"] for r in candidates if r["creator"]["id"] == selected),
                None,
            ),
        }
