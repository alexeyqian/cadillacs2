"""
data/object_pool.py
====================
Generic object pool. Avoids GC spikes for VFXObject, Projectile, DamageNumber.
"""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


class ObjectPool:
    """
    Pre-allocates a fixed set of objects and recycles them.

    Usage:
        pool = ObjectPool(factory=lambda: VFXObject(str(uuid4())), size=32)
        obj  = pool.acquire()
        # ... use obj ...
        pool.release(obj)    # calls obj.reset() and returns to pool
    """

    def __init__(self, factory: Callable[[], T], size: int) -> None:
        self._factory  = factory
        self._available: list[T] = [factory() for _ in range(size)]
        self._in_use:   list[T] = []

    def acquire(self) -> T:
        if self._available:
            obj = self._available.pop()
        else:
            # Pool exhausted — create a new one (degrades to normal allocation)
            obj = self._factory()
        self._in_use.append(obj)
        return obj

    def release(self, obj: T) -> None:
        if obj in self._in_use:
            self._in_use.remove(obj)
        if hasattr(obj, "reset"):
            obj.reset()  # type: ignore[attr-defined]
        if obj not in self._available:
            self._available.append(obj)

    @property
    def available_count(self) -> int:
        return len(self._available)

    @property
    def in_use_count(self) -> int:
        return len(self._in_use)
