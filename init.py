from typing import Generic, Any, Annotated, TypeVar, Literal
from pydantic.dataclasses import dataclass

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")
X = TypeVar("X")
Y = TypeVar("Y")
Z = TypeVar("Z")


class Foo(Generic[T]):
    pass


class Child(Foo[U]):
    pass


class GrandChild(Child[V]):
    pass


class Specific(Foo[int]):
    pass


class SpecificGrandChild(Specific):
    pass


class Extra(Foo[U], Generic[U, V]):
    pass


class Unrelated(Foo[int], Generic[V]):
    pass


class Disordered(Foo[U], Generic[T, U, V]):
    pass


class P(Generic[T, U]):
    pass


class L(P[int, V]):
    pass


class R(P[W, str]):
    pass


# class R2(R[V]):
#     pass


class C(L[str], R[int]):
    pass


class F(Generic[T, U]):
    pass


class FL(F[str, V], Generic[V, W]):
    pass


class FR(F[X, int], Generic[Y, X]):
    pass


class FC(FL[int, Z], FR[Z, str]):
    pass
