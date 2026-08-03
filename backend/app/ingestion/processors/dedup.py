from __future__ import annotations

import hashlib


def compute_content_hash(content: str) -> str:
    normalized = " ".join(content.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
