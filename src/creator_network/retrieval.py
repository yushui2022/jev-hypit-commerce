"""Deterministic lexical retrieval and rank fusion. Scores are not confidence."""

import math
import re
from collections import Counter


def tokenize(text):
    words = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower())
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    return words + [chinese[i : i + 2] for i in range(len(chinese) - 1)]


def document(item):
    return " ".join(
        [item["name"], item.get("description", ""), " ".join(item.get("tags", []))]
    )


def bm25(query, items):
    docs = [Counter(tokenize(document(x))) for x in items]
    terms = set(tokenize(query))
    N = len(items)
    avg = sum(sum(d.values()) for d in docs) / max(N, 1)
    df = {t: sum(t in d for d in docs) for t in terms}
    result = []
    for item, d in zip(items, docs):
        length = sum(d.values())
        score = 0.0
        matches = []
        for t in terms:
            tf = d[t]
            if tf:
                score += (
                    math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
                    * tf
                    * 2.2
                    / (tf + 1.2 * (0.25 + 0.75 * length / max(avg, 1)))
                )
                matches.append(t)
        if score > 0:
            result.append(
                {
                    "creator": item,
                    "score": score,
                    "matched_terms": sorted(matches),
                    "sources": ["bm25"],
                }
            )
    return sorted(result, key=lambda r: (-r["score"], r["creator"]["id"]))


def fuse(lexical, dense, k=60):
    rows = {}
    for source, ranking in [("bm25", lexical), ("dense", dense)]:
        for rank, row in enumerate(ranking, 1):
            id = row["creator"]["id"]
            item = rows.setdefault(
                id,
                {
                    "creator": row["creator"],
                    "score": 0.0,
                    "sources": [],
                    "matched_terms": [],
                },
            )
            item["score"] += 1 / (k + rank)
            item["sources"].append(source)
            item["matched_terms"] = (
                row.get("matched_terms", []) or item["matched_terms"]
            )
    return sorted(rows.values(), key=lambda r: (-r["score"], r["creator"]["id"]))
