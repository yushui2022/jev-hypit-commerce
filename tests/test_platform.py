import json, time
from concurrent.futures import ThreadPoolExecutor
import httpx, pytest
from fastapi.testclient import TestClient
from creator_network.config import Settings
from creator_network.models import Item
from creator_network.store import Store, Conflict
from creator_network.pipeline import MatchingPipeline
from creator_network.worker import Worker
from creator_network.api import create_app
from creator_network.decision import JevSelector, ProviderError
from creator_network.rendering import approved_snapshot
from creator_network.media import media_path
from creator_network.retrieval import bm25, fuse
from pathlib import Path


@pytest.fixture
def setup(tmp_path):
    settings = Settings(data=tmp_path, worker_enabled=False, jev_key="", api_token="")
    store = Store(settings.database)
    rows = [
        Item(
            id="p",
            kind="product",
            name="Desk speaker",
            description="wireless audio speaker",
        ).model_dump(),
        Item(
            id="tech",
            kind="creator",
            name="Tech creator",
            description="wireless audio speaker desk gadgets",
        ).model_dump(),
        Item(
            id="beauty",
            kind="creator",
            name="Beauty creator",
            description="skincare serum makeup",
        ).model_dump(),
        Item(
            id="wrong-market", kind="creator", name="Speaker audio", market="UK"
        ).model_dump(),
    ]
    store.upsert(rows)
    return settings, store


def request(engine="baseline"):
    return {
        "product_id": "p",
        "top_k": 8,
        "engine": engine,
        "market": None,
        "language": None,
    }


def completed(setup):
    settings, store = setup
    j = store.enqueue("match", request())
    Worker(settings, store).once()
    return store.job(j["id"])


def test_atomic_claim_and_idempotency(setup):
    _, s = setup
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = list(
            pool.map(lambda _: s.enqueue("match", request(), "same"), range(12))
        )
    assert len({x["id"] for x in jobs}) == 1
    with pytest.raises(Conflict):
        s.enqueue("match", request("jev"), "same")
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda i: s.claim(str(i)), range(8)))
    assert sum(x is not None for x in claims) == 1


def test_expired_lease_requires_explicit_retry(setup):
    _, s = setup
    j = s.enqueue("match", request())
    s.claim("old", lease=-1)
    assert s.claim("new") is None
    assert s.job(j["id"])["error"] == "worker_lease_expired"
    assert not s.finish(j["id"], "old", result={"wrong": True})
    s.retry(j["id"])
    assert s.claim("new")["attempts"] == 2
    assert s.finish(j["id"], "new", error="upstream")
    s.retry(j["id"])
    s.claim("third")
    s.finish(j["id"], "third", error="upstream")
    with pytest.raises(Conflict):
        s.retry(j["id"])


def test_filter_score_and_snapshot_review(setup):
    settings, s = setup
    j = completed(setup)
    r = j["result"]
    assert r["decision"]["creator_id"] == "tech" and r["decision"]["confidence"] is None
    assert [x["creator"]["id"] for x in r["candidates"]] == ["tech"]
    with pytest.raises(Conflict):
        approved_snapshot(s, j["id"])
    with pytest.raises(ValueError):
        s.review(j["id"], "approve", "wrong-market", "")
    changed = s.item("tech")
    changed["description"] = "changed later"
    s.upsert([changed])
    s.review(j["id"], "approve", "tech", "reviewed")
    snap = approved_snapshot(s, j["id"])
    assert snap["creator"]["description"] != "changed later"
    s.review(j["id"], "reject", None, "wrong context")
    with pytest.raises(Conflict):
        approved_snapshot(s, j["id"])
    assert len([e for e in s.events(j["id"]) if e["event"] == "reviewed"]) == 2


def test_no_matching_candidates(setup):
    settings, s = setup
    r = MatchingPipeline(settings, s).run({**request(), "market": "JP"})
    assert r["candidates"] == [] and r["selected_creator"] is None


def test_provider_failure_does_not_become_baseline(setup):
    settings, s = setup
    j = s.enqueue("match", request("jev"))
    Worker(settings, s).once()
    assert s.job(j["id"])["status"] == "failed" and s.job(j["id"])["result"] is None


@pytest.mark.parametrize(
    "answer",
    [
        {"choice": "invented", "confidence": 0.9},
        {"choice": "tech", "confidence": 1.1},
        {"choice": "tech", "confidence": True},
        {"choice": "tech", "confidence": None},
    ],
)
def test_jev_validates_enum_and_confidence(setup, answer):
    settings, s = setup
    candidates = MatchingPipeline(settings, s).run(request())["candidates"]
    selector = JevSelector(
        "test",
        httpx.MockTransport(
            lambda _: httpx.Response(200, json={"answers": {"creator": answer}})
        ),
    )
    with pytest.raises(ProviderError):
        selector.choose(s.item("p"), candidates)


def test_jev_success_keeps_provenance(setup):
    settings, s = setup

    def handler(req):
        body = json.loads(req.content)
        assert body["questions"]["creator"]["type"] == "choice"
        assert list(body["questions"]["creator"]["criteria"]) == ["tech"]
        return httpx.Response(
            200, json={"answers": {"creator": {"choice": "tech", "confidence": 0.88}}}
        )

    pipeline = MatchingPipeline(
        settings, s, JevSelector("test", httpx.MockTransport(handler))
    )
    r = pipeline.run(request("jev"))
    assert r["decision"]["provider"] == "jev" and r["decision"]["confidence"] == 0.88
    assert r["review"]["status"] == "pending"


def test_api_auth_import_review_and_idempotency(setup):
    settings, s = setup
    settings.api_token = "local-test"
    app = create_app(settings)
    with TestClient(app) as client:
        assert client.get("/api/catalog").status_code == 401
        client.headers["Authorization"] = "Bearer local-test"
        assert client.get("/api/catalog").status_code == 200
        assert (
            client.post(
                "/api/catalog",
                json={"items": [{"id": "bad/path", "kind": "product", "name": "bad"}]},
            ).status_code
            == 422
        )
        r = client.post(
            "/api/matches", json=request(), headers={"Idempotency-Key": "one"}
        )
        assert r.status_code == 202
        j = r.json()
        assert (
            client.post(
                "/api/matches", json=request(), headers={"Idempotency-Key": "one"}
            ).json()["id"]
            == j["id"]
        )
        assert (
            client.post(
                "/api/matches", json=request("jev"), headers={"Idempotency-Key": "one"}
            ).status_code
            == 409
        )
        assert (
            client.post("/api/renders", json={"match_job_id": j["id"]}).status_code
            == 409
        )
        app.state.worker.once()
        assert (
            client.post(
                "/api/matches/" + j["id"] + "/review",
                json={"action": "approve", "creator_id": "tech"},
            ).status_code
            == 200
        )
        r = client.post("/api/renders", json={"match_job_id": j["id"]})
        assert r.status_code == 202
        assert r.json()["payload"]["creator"]["id"] == "tech"
        assert (
            client.get("/api/jobs/" + j["id"] + "/files/guanyi.mp4").status_code == 404
        )
        assert client.get("/api/jobs/missing").status_code == 404


def test_media_paths_and_symlinks(tmp_path):
    assets = tmp_path / "examples/assets"
    assets.mkdir(parents=True)
    (assets / "safe.png").write_bytes(b"test")
    secret = tmp_path / "private.png"
    secret.write_bytes(b"secret")
    (assets / "link.png").symlink_to(secret)
    assert media_path(tmp_path, "examples/assets/safe.png").name == "safe.png"
    for path in [
        "private.png",
        "examples/assets/../../private.png",
        "examples/assets/link.png",
        "examples/assets/.env",
    ]:
        with pytest.raises(KeyError):
            media_path(tmp_path, path)


def test_import_rollback(setup):
    _, s = setup
    new = Item(id="new", kind="product", name="x").model_dump()
    conflict = Item(id="tech", kind="product", name="x").model_dump()
    with pytest.raises(Conflict):
        s.upsert([new, conflict])
    with pytest.raises(KeyError):
        s.item("new")


def test_fusion_rewards_agreement():
    rows = [{"creator": {"id": x}, "score": 1} for x in ["a", "b", "c"]]
    result = fuse(rows[:2], [rows[1], rows[2]])
    assert result[0]["creator"]["id"] == "b" and result[0]["sources"] == [
        "bm25",
        "dense",
    ]
