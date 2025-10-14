from typing import Generic, TypeVar, Callable

T = TypeVar("T")
U = TypeVar("U")

class Maybe(Generic[T]):
    def __init__(self, value: T | None):
        self._value = value

    def is_nothing(self) -> bool:
        return self._value is None

    def map(self, func: Callable[[T], U]) -> "Maybe[U]":
        if self.is_nothing():
            return Maybe(None)
        return Maybe(func(self._value))

    def get_or_else(self, default: U) -> T | U:
        return self._value if not self.is_nothing() else default

    def __repr__(self):
        return f"Just({self._value})" if not self.is_nothing() else "Nothing"
