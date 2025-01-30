from scanspec.core import (
    UnsupportedSubclass,
    discriminated_union_of_subclasses,
)
from pydantic import TypeAdapter
import pytest
from pydantic.dataclasses import dataclass
from typing import Generic, TypeVar, Annotated, Any

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

B = TypeVar("B", int, float)



@discriminated_union_of_subclasses
class Parent(Generic[T]):
    pass


@dataclass
class Child(Parent[U]):
    a: U

@dataclass
class AnnotatedChild(Parent[Annotated[U, "comment"]]):
    b: U

@dataclass
class GrandChild(Child[V]):
    # TODO: subclasses with fields?
    pass


with pytest.warns(UnsupportedSubclass):
    @dataclass
    class Specific(Parent[int]):
        b: int


with pytest.warns(UnsupportedSubclass):
    @dataclass
    class SubSpecific(Specific):
        pass


with pytest.warns(UnsupportedSubclass):
    @dataclass
    class ExtraGeneric(Parent[U], Generic[U, V]):
        c: U
        d: V


with pytest.warns(UnsupportedSubclass):
    @dataclass
    class UnrelatedGeneric(Parent[int], Generic[U]):
        e: int
        f: U


with pytest.warns(UnsupportedSubclass):
    @dataclass
    class DisorderedGeneric(Parent[U], Generic[T, U, V]):
        g: T
        h: U
        i: V

with pytest.warns(UnsupportedSubclass):
    @dataclass
    class Ambiguous(Parent[int | U], Generic[U]):
        a: U


with pytest.warns(UnsupportedSubclass):
    @dataclass
    class UnmarkedChild(Parent): # type: ignore we're testing the bad type annotations
        a: int


with pytest.warns(UnsupportedSubclass):
    # Adding bounds to the generic parameter is not supported
    @dataclass
    class ConstrainedChild(Parent[B]):
        cc: B


@discriminated_union_of_subclasses
class NonGenericParent:
    pass

@dataclass
class NonGenericChild(NonGenericParent):
    a: int
    b: float

with pytest.warns(UnsupportedSubclass):
    @dataclass
    class NewGenerics(NonGenericParent, Generic[T]):
        a: T


def deserialize(target: type[Any], source: Any) -> Any:
    return TypeAdapter(target).validate_python(source) # type: ignore

def test_child():
    ch = deserialize(Parent[int], {"type": "Child", "a": "42"})
    assert ch.a == 42

    ch = deserialize(Parent[str], {"type": "Child", "a": "42"})
    assert ch.a == "42"

    ch = deserialize(Parent[list[int]], {'type': 'Child', 'a': ['1', '2', '3']})
    assert ch.a == [1, 2, 3]

def test_annotated_child():
    ch = deserialize(Parent[int], {"type": "AnnotatedChild", "b": "42"})
    assert ch.b == 42

@pytest.mark.xfail(reason="Pydantic #11363")
def test_grandchild():
    gc: Parent[int] = GrandChild(a='43')
    print(gc)
    ch = deserialize(Parent[int], {"type": "GrandChild", "a": "42"})
    assert ch.a == 42

def test_non_generic_child():
    ngc = deserialize(NonGenericParent,
        {"type": "NonGenericChild", "a": "42", "b": "3.14"}
    )
    assert ngc.a == 42
    assert ngc.b == pytest.approx(3.14)
