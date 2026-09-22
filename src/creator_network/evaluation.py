import json

from .retrieval import bm25


def evaluate(settings):
    fixture = json.loads((settings.root / "evals/retrieval.json").read_text())
    rr = []
    recall = []
    p1 = []
    details = []
    for query in fixture["queries"]:
        ranked = [r["creator"]["id"] for r in bm25(query["text"], fixture["creators"])]
        relevant = set(query["relevant"])
        hit = next((i for i, id in enumerate(ranked, 1) if id in relevant), None)
        rr.append(1 / hit if hit else 0)
        recall.append(len(set(ranked[:3]) & relevant) / len(relevant))
        p1.append(float(bool(ranked) and ranked[0] in relevant))
        details.append(
            {"query": query["text"], "ranked": ranked, "relevant": query["relevant"]}
        )
    return {
        "fixture": fixture["description"],
        "queries": len(rr),
        "engine": "bm25",
        "precision_at_1": sum(p1) / len(p1),
        "recall_at_3": sum(recall) / len(recall),
        "mrr": sum(rr) / len(rr),
        "details": details,
    }
