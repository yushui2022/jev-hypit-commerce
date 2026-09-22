"""Explicit demo fixtures. Showcase creator personas are synthetic editorial profiles."""

import json

from .models import Item

PROFILES = {
    "beauty": "beauty skincare cosmetics serum body care makeup wellness personal care",
    "style": "fashion style perfume fragrance jewelry bag accessories clothing",
    "active": "fitness outdoor sports hydration tumbler bottle active lifestyle",
    "home": "home kitchen household cooking cleaning tumbler organization",
    "tech": "technology electronics speaker headphones audio phone desk gadget",
}


def seed(settings, store, showcase=False):
    rows = []
    if showcase:
        text = (settings.root / "packages/hd-fast/src/content.ts").read_text()
        products = json.JSONDecoder().raw_decode(text.split("=", 1)[1].lstrip())[0]
        for p in products:
            rows.append(
                Item(
                    id="product-" + str(p["index"]).zfill(3),
                    kind="product",
                    name=p["short_name"],
                    description=p.get("visual_features", "")
                    + " "
                    + p.get("category_en", ""),
                    tags=[p["profile"], p.get("category_en", "product")],
                    image="productions/hd-fast/" + p["image"],
                ).model_dump()
            )
        for profile, description in PROFILES.items():
            for cell in range(20):
                scene = [
                    "bright studio tutorials",
                    "everyday home routine",
                    "outdoor lifestyle",
                    "desk close-up demonstrations",
                ][cell % 4]
                style = [
                    "step-by-step explainer",
                    "casual first look",
                    "comparison and details",
                    "minimal aesthetic showcase",
                    "practical how-to",
                ][cell // 4]
                rows.append(
                    Item(
                        id=f"{profile}-{cell:02}",
                        kind="creator",
                        name=f"{profile.title()} Creator {cell + 1:02}",
                        description=f"Fictional US-market English-language UGC persona. Editorial specialization: {description}. Assigned scene: {scene}. Content format: {style}.",
                        tags=description.split(),
                        image=f"productions/hd-fast/assets/avatars/library-{profile}.png",
                        sheet_cell=cell,
                    ).model_dump()
                )
    else:
        catalog = json.loads((settings.root / "examples/catalog.json").read_text())
        for p in catalog["products"]:
            rows.append(
                Item(
                    id=p["id"],
                    kind="product",
                    name=p["name"],
                    description=p["visual_features"],
                    image="examples/" + p["image"],
                ).model_dump()
            )
        for c in catalog["avatars"]:
            rows.append(
                Item(
                    id=c["id"],
                    kind="creator",
                    name=c["id"].title() + " Creator",
                    description=c["description"],
                    tags=PROFILES[c["id"]].split(),
                    image="examples/" + c["image"],
                ).model_dump()
            )
    store.upsert(rows)
    return {
        "imported": len(rows),
        "dataset": "showcase" if showcase else "fictional-demo",
    }
