"""SQLite WAL repository and leased jobs. Transactions delimit state transitions."""

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
            INSERT OR IGNORE INTO schema_version VALUES(1);
            CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,kind TEXT NOT NULL,data TEXT NOT NULL,updated REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS items_kind ON items(kind);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,request_hash TEXT NOT NULL,
            idempotency_key TEXT UNIQUE,status TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,owner TEXT,lease_until REAL,
            result TEXT,error TEXT,created REAL NOT NULL,updated REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS jobs_ready ON jobs(status,created);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,event TEXT NOT NULL,data TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,action TEXT NOT NULL,creator_id TEXT,note TEXT NOT NULL,created REAL NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def upsert(self, items):
        if len({x["id"] for x in items}) != len(items):
            raise ValueError("Duplicate IDs in import")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for item in items:
                existing = db.execute(
                    "SELECT kind FROM items WHERE id=?", (item["id"],)
                ).fetchone()
                if existing and existing["kind"] != item["kind"]:
                    raise Conflict("An ID cannot change its item kind")
                db.execute(
                    "INSERT INTO items VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data,updated=excluded.updated",
                    (
                        item["id"],
                        item["kind"],
                        json.dumps(item, ensure_ascii=False),
                        time.time(),
                    ),
                )

    def items(self, kind=None):
        with self.connect() as db:
            rows = db.execute(
                "SELECT data FROM items"
                + (" WHERE kind=?" if kind else "")
                + " ORDER BY id",
                (kind,) if kind else (),
            ).fetchall()
        return [json.loads(x["data"]) for x in rows]

    def item(self, id):
        with self.connect() as db:
            r = db.execute("SELECT data FROM items WHERE id=?", (id,)).fetchone()
        if not r:
            raise KeyError(id)
        return json.loads(r["data"])

    @staticmethod
    def _job(row):
        if not row:
            raise KeyError("Job not found")
        out = dict(row)
        for k in ("payload", "result"):
            out[k] = json.loads(out[k]) if out[k] else None
        out.pop("request_hash", None)
        out.pop("owner", None)
        return out

    @staticmethod
    def event(db, id, event, data=None):
        db.execute(
            "INSERT INTO events(job_id,event,data,created) VALUES(?,?,?,?)",
            (id, event, json.dumps(data or {}, ensure_ascii=False), time.time()),
        )

    def enqueue(self, kind, payload, key=None):
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256((kind + body).encode()).hexdigest()
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if key:
                old = db.execute(
                    "SELECT * FROM jobs WHERE idempotency_key=?", (key,)
                ).fetchone()
                if old:
                    if old["request_hash"] != digest:
                        raise Conflict(
                            "Idempotency key was already used for another request"
                        )
                    return self._job(old)
            id = uuid.uuid4().hex
            db.execute(
                "INSERT INTO jobs(id,kind,payload,request_hash,idempotency_key,status,created,updated) VALUES(?,?,?,?,?,?,?,?)",
                (id, kind, body, digest, key, "queued", now, now),
            )
            self.event(db, id, "queued")
        return self.job(id)

    def job(self, id):
        with self.connect() as db:
            r = db.execute("SELECT * FROM jobs WHERE id=?", (id,)).fetchone()
        return self._job(r)

    def jobs(self, limit=100):
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM jobs ORDER BY created DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._job(x) for x in rows]

    def events(self, id):
        self.job(id)
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE job_id=? ORDER BY seq", (id,)
            ).fetchall()
        return [{**dict(x), "data": json.loads(x["data"])} for x in rows]

    def claim(self, owner, lease=90):
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # An interrupted external call may have been charged: require explicit retry, never auto-submit again.
            expired = db.execute(
                "SELECT id FROM jobs WHERE status='running' AND lease_until<?", (now,)
            ).fetchall()
            for row in expired:
                db.execute(
                    "UPDATE jobs SET status='failed',error='worker_lease_expired',owner=NULL,updated=? WHERE id=?",
                    (now, row["id"]),
                )
                self.event(db, row["id"], "lease_expired")
            row = db.execute(
                "SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1"
            ).fetchone()
            if not row:
                return None
            db.execute(
                "UPDATE jobs SET status='running',attempts=attempts+1,owner=?,lease_until=?,updated=? WHERE id=?",
                (owner, now + lease, now, row["id"]),
            )
            self.event(db, row["id"], "running", {"attempt": row["attempts"] + 1})
        return self.job(row["id"])

    def heartbeat(self, id, owner, lease=90):
        with self.connect() as db:
            return (
                db.execute(
                    "UPDATE jobs SET lease_until=? WHERE id=? AND owner=? AND status='running'",
                    (time.time() + lease, id, owner),
                ).rowcount
                == 1
            )

    def finish(self, id, owner, result=None, error=None):
        with self.connect() as db:
            changed = db.execute(
                "UPDATE jobs SET status=?,result=?,error=?,owner=NULL,lease_until=NULL,updated=? WHERE id=? AND owner=? AND status='running'",
                (
                    "failed" if error else "completed",
                    json.dumps(result, ensure_ascii=False)
                    if result is not None
                    else None,
                    error,
                    time.time(),
                    id,
                    owner,
                ),
            ).rowcount
            if changed:
                self.event(
                    db,
                    id,
                    "failed" if error else "completed",
                    {"error": error} if error else {},
                )
        return bool(changed)

    def retry(self, id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            r = db.execute("SELECT * FROM jobs WHERE id=?", (id,)).fetchone()
            if not r:
                raise KeyError(id)
            if r["status"] != "failed" or r["attempts"] >= 3:
                raise Conflict(
                    "Only failed jobs with fewer than three attempts can retry"
                )
            db.execute(
                "UPDATE jobs SET status='queued',error=NULL,updated=? WHERE id=?",
                (time.time(), id),
            )
            self.event(db, id, "retry_requested")
        return self.job(id)

    def review(self, id, action, creator_id, note):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE id=?", (id,)).fetchone()
            if not row:
                raise KeyError(id)
            if row["kind"] != "match" or row["status"] != "completed":
                raise Conflict("Only completed matching jobs can be reviewed")
            result = json.loads(row["result"])
            valid = {x["creator"]["id"] for x in result["candidates"]}
            chosen = creator_id or result["decision"].get("creator_id")
            if action == "approve" and chosen not in valid:
                raise ValueError("Select a candidate from this decision snapshot")
            result["review"] = {
                "status": "approved" if action == "approve" else "rejected",
                "creator_id": chosen,
                "note": note,
                "at": time.time(),
            }
            db.execute(
                "UPDATE jobs SET result=?,updated=? WHERE id=?",
                (json.dumps(result, ensure_ascii=False), time.time(), id),
            )
            db.execute(
                "INSERT INTO feedback(job_id,action,creator_id,note,created) VALUES(?,?,?,?,?)",
                (id, action, chosen, note, time.time()),
            )
            self.event(db, id, "reviewed", result["review"])
        return self.job(id)
