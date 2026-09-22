"""Approved immutable decision snapshot -> Hypit -> two branded deliverables."""

import json
import subprocess
import sys

from .media import media_path
from .store import Conflict


def approved_snapshot(store, id):
    job = store.job(id)
    result = job.get("result") or {}
    if (
        job["kind"] != "match"
        or job["status"] != "completed"
        or result.get("review", {}).get("status") != "approved"
    ):
        raise Conflict("Approve a completed match before rendering")
    creator = next(
        x["creator"]
        for x in result["candidates"]
        if x["creator"]["id"] == result["review"]["creator_id"]
    )
    return {
        "match_job_id": id,
        "product": result["product"],
        "creator": creator,
        "review": result["review"],
    }


def render(settings, job):
    dest = settings.data / "jobs" / job["id"]
    dest.mkdir(parents=True, exist_ok=True)
    snapshot = job["payload"]
    p = snapshot["product"]
    c = snapshot["creator"]
    product = media_path(settings.root, p["image"])
    avatar = media_path(settings.root, c["image"])
    if c.get("sheet_cell") is not None:
        from PIL import Image

        with Image.open(avatar) as im:
            cell = c["sheet_cell"]
            w = im.width / 4
            h = im.height / 5
            im.crop(
                (
                    round(cell % 4 * w),
                    round(cell // 4 * h),
                    round((cell % 4 + 1) * w),
                    round((cell // 4 + 1) * h),
                )
            ).save(dest / "avatar.png")
        avatar = dest / "avatar.png"
    storyboard = {
        "pairs": [
            {
                "product": {**p, "image": str(product)},
                "avatar": {**c, "image": str(avatar)},
            }
        ]
    }
    source = dest / "storyboard.json"
    source.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2))
    with (dest / "render.log").open("w") as log:
        # Each attempt has a unique output directory; interrupted renders cannot collide.
        out = dest / f"attempt-{job['attempts']}"
        subprocess.run(
            [
                sys.executable,
                str(settings.root / "render.py"),
                "build",
                str(source),
                "--output",
                str(out),
            ],
            cwd=settings.root,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=1200,
        )
        files = []
        for brand, width in [("guanyi", 170), ("yeadon", 145)]:
            name = f"{brand}.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(out / "video.mp4"),
                    "-i",
                    str(
                        settings.root
                        / f"productions/hd-fast/assets/branding/{brand}.png"
                    ),
                    "-filter_complex",
                    f"[1:v]scale={width}:-1[logo];[0:v][logo]overlay=W-w-35:H-h-25[v]",
                    "-map",
                    "[v]",
                    "-map",
                    "0:a?",
                    "-c:v",
                    "libx264",
                    "-crf",
                    "18",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(dest / name),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=180,
            )
            files.append({"brand": brand, "url": f"/api/jobs/{job['id']}/files/{name}"})
    return {
        "files": files,
        "match_job_id": snapshot["match_job_id"],
        "review": snapshot["review"],
    }
