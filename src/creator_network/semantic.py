"""Optional real FastEmbed + Qdrant adapter; no synthetic vectors in runtime."""

import hashlib
import json
import uuid

from .retrieval import document


class SemanticIndex:
    def __init__(self, settings, client=None, embedder=None):
        from fastembed import TextEmbedding
        from qdrant_client import QdrantClient, models

        self.models = models
        self.settings = settings
        self.client = client or (
            QdrantClient(
                url=settings.qdrant_url, api_key=settings.qdrant_key or None, timeout=20
            )
            if settings.qdrant_url
            else QdrantClient(path=str(settings.data / "qdrant"))
        )
        self.model = embedder or TextEmbedding(
            model_name=settings.embedding_model, cache_dir=str(settings.data / "models")
        )
        self.collection = (
            "creator_"
            + hashlib.sha256(settings.embedding_model.encode()).hexdigest()[:12]
        )
        self.fingerprint = None

    def rank(self, query, items, limit=30):
        if not items:
            return []
        signature = hashlib.sha256(
            json.dumps(items, sort_keys=True).encode()
        ).hexdigest()
        vectors = None
        m = self.models
        if signature != self.fingerprint:
            vectors = [
                v.tolist() for v in self.model.embed([document(x) for x in items])
            ]
            if not self.client.collection_exists(self.collection):
                self.client.create_collection(
                    self.collection,
                    vectors_config=m.VectorParams(
                        size=len(vectors[0]), distance=m.Distance.COSINE
                    ),
                )
            points = [
                m.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, item["id"])),
                    vector=vec,
                    payload={"creator_id": item["id"]},
                )
                for item, vec in zip(items, vectors)
            ]
            self.client.upsert(self.collection, points, wait=True)
            self.fingerprint = signature
        vec = next(iter(self.model.query_embed(query))).tolist()
        byid = {x["id"]: x for x in items}
        # Restrict to current eligible IDs: stale or deactivated points cannot enter the result.
        filt = m.Filter(
            must=[m.FieldCondition(key="creator_id", match=m.MatchAny(any=list(byid)))]
        )
        points = self.client.query_points(
            self.collection,
            query=vec,
            query_filter=filt,
            limit=limit,
            with_payload=True,
        ).points
        return [
            {
                "creator": byid[p.payload["creator_id"]],
                "score": p.score,
                "sources": ["dense"],
            }
            for p in points
            if p.payload["creator_id"] in byid
        ]
