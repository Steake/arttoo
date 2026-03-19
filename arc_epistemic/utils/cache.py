from __future__ import annotations

from collections.abc import Callable


class SimpleCache:
    def __init__(self) -> None:
        self._store: dict[tuple[object, ...], object] = {}

    def get_or_compute(self, key: tuple[object, ...], factory: Callable[[], object]) -> object:
        if key not in self._store:
            self._store[key] = factory()
        return self._store[key]
