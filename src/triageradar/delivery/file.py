"""Atomic local file delivery."""

import json
import os
from pathlib import Path

from triageradar.models.digest import DigestDocument
from triageradar.rendering.html import render


def publish(digest: DigestDocument, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(
        output_dir / "digest.json",
        json.dumps(digest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(output_dir / "digest.html", render(digest))


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)
