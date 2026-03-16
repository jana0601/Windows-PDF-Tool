from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pymupdf as fitz


@dataclass
class DocumentState:
    file_path: str | None = None
    document: fitz.Document | None = None
    current_page: int = 0
    zoom: float = 1.0
    actions: list[dict[str, Any]] = field(default_factory=list)
    redo_actions: list[dict[str, Any]] = field(default_factory=list)

    def reset_actions(self) -> None:
        self.actions.clear()
        self.redo_actions.clear()

    @property
    def has_document(self) -> bool:
        return self.document is not None
