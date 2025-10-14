from typing import Generic, TypeVar, Callable

E = TypeVar("E")
T = TypeVar("T")
U = TypeVar("U")

class Either(Generic[E, T]):
    def __init__(self, is_right: bool, value: E | T):
        self.is_right = is_right
        self.value = value

    @staticmethod
    def right(value: T) -> "Either[E, T]":
        return Either(True, value)

    @staticmethod
    def left(value: E) -> "Either[E, T]":
        return Either(False, value)

    def map(self, func: Callable[[T], U]) -> "Either[E, U]":
        if self.is_right:
            return Either.right(func(self.value))
        return Either.left(self.value)

    def get_or_else(self, default: T) -> T:
        return self.value if self.is_right else default

    def __repr__(self):
        return f"Right({self.value})" if self.is_right else f"Left({self.value})"
