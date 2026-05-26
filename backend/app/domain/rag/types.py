from __future__ import annotations

import enum


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class CitationStatus(str, enum.Enum):
    UNVALIDATED = "unvalidated"
