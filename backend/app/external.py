from collections.abc import Iterator
from typing import Any, Protocol


class ExternalSourceAdapter(Protocol):
    """P0 contract only; concrete external connectors belong to P1."""

    def discover(self, cursor: str | None = None) -> Iterator[str]: ...

    def fetch_item(self, external_id: str) -> dict[str, Any]: ...

    def normalize(self, raw_item: dict[str, Any]) -> dict[str, Any]: ...

    def get_cursor(self) -> str | None: ...
