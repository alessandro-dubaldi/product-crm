import random
from typing import TypeVar

T = TypeVar("T")


def sample(pool: list[T], n: int) -> list[T]:
    """Random sample of n items from pool without replacement."""
    return random.sample(pool, min(n, len(pool)))
