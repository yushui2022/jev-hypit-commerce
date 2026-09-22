import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    root: Path = field(
        default_factory=lambda: Path(
            os.getenv("CREATOR_ROOT", Path(__file__).resolve().parents[2])
        ).resolve()
    )
    data: Path = field(
        default_factory=lambda: Path(os.getenv("CREATOR_DATA", "data")).resolve()
    )
    api_token: str = field(default_factory=lambda: os.getenv("CREATOR_API_TOKEN", ""))
    jev_key: str = field(default_factory=lambda: os.getenv("JEV_API_KEY", ""))
    retrieval: str = field(
        default_factory=lambda: os.getenv("CREATOR_RETRIEVAL", "lexical")
    )
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", ""))
    qdrant_key: str = field(default_factory=lambda: os.getenv("QDRANT_API_KEY", ""))
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    confidence_threshold: float = 0.75
    worker_enabled: bool = True

    @property
    def database(self):
        return self.data / "creator-network.sqlite3"
