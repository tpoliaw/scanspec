from scanspec.core import (
    InconsistentTypeWarning,
    discriminated_union_of_subclasses,
    _subclass_spec,
    _build_subclass,
    _get_origin,
)
from pydantic import TypeAdapter
import pytest
from pydantic.dataclasses import dataclass
from typing import Generic, TypeVar, Annotated, Any

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


@discriminated_union_of_subclasses
class Parent(Generic[T]):
    pass


@dataclass
class Child(Parent[U]):
    a: U


@dataclass
class GrandChild(Child[V]):
    # TODO: subclasses with fields?
    pass


@dataclass
class Specific(Parent[int]):
    b: int


@dataclass
class SubSpecific(Specific):
    # TODO: subclasses with fields?
    pass


@dataclass
class ExtraGeneric(Parent[U], Generic[U, V]):
    c: U
    d: V


@dataclass
class UnrelatedGeneric(Parent[int], Generic[U]):
    e: int
    f: U


@dataclass
class DisorderedGeneric(Parent[U], Generic[T, U, V]):
    g: T
    h: U
    i: V

@dataclass
class AmbiguousChild(Parent[int | U], Generic[U]):
    a: U


with pytest.warns(InconsistentTypeWarning, match="does not have enough type parameters"):
    @dataclass
    class UnmarkedChild(Parent): # type: ignore we're testing the bad type annotations
        a: int


A = TypeVar("A", int, float, str)
B = TypeVar("B", int, float)


@discriminated_union_of_subclasses
class ConstrainedParent(Generic[A]):
    pass


@dataclass
class ConstrainedChild(ConstrainedParent[B]):
    cc: B


@discriminated_union_of_subclasses
class NonGenericParent:
    pass


@dataclass
class NonGenericChild(NonGenericParent):
    a: int
    b: float


def deserialize(target: type[Any], source: Any) -> Any:
    return TypeAdapter(target).validate_python(source) # type: ignore

def test_child():
    ch = deserialize(Parent[int], {"type": "Child", "a": "42"})
    assert ch.a == 42

    ch = deserialize(Parent[str], {"type": "Child", "a": "42"})
    assert ch.a == "42"


def test_specific():
    ch = deserialize(Parent[int], {"type": "Specific", "b": "42"})
    assert ch.b == 42

    with pytest.raises(Exception):
        ch = deserialize(Parent[str], {"type": "Specific", "b": "42"})
        print(ch)


def test_extra_generic():
    ch = deserialize(Parent[int],
        {"type": "ExtraGeneric", "c": "42", "d": "foo"}
    )
    assert ch.c == 42
    assert ch.d == "foo"


def test_unrelated_generic():
    ch = deserialize(Parent[int],
        {"type": "UnrelatedGeneric", "e": "42", "f": "foo"}
    )
    assert ch.e == 42
    assert ch.f == "foo"

    with pytest.raises(Exception):
        ch = deserialize(Parent[str],
            {"type": "UnrelatedGeneric", "e": "42", "f": "foo"}
        )


def test_disordered_generic():
    ch = deserialize(Parent[int],
        {
            "type": "DisorderedGeneric",
            "g": [1, 2, 3],
            "h": "42",
            "i": {"arbitrary": "map"},
        }
    )
    assert ch.g == [1, 2, 3]
    assert ch.h == 42
    assert ch.i == {"arbitrary": "map"}


def test_unmarked_child():
    ch = deserialize(Parent[int], {"type": "UnmarkedChild", "a": "23"})
    assert ch.a == 23

def test_ambiguous_child():
    # this test is ambiguous as both 42 and '42' would be valid but record the
    # one that works here so at least we know it stays consistent
    spec ={'type': 'AmbiguousChild', 'a': '42'}
    ch = deserialize(Parent[int], spec)
    assert ch.a == '42'

    ch = deserialize(Parent[str], spec)
    assert ch.a == '42'

    ch = deserialize(Parent[float], spec)
    assert ch.a == 42.0


@pytest.mark.parametrize(
    "typ,origin",
    [
        (int, int),
        (list[int], list),
        (list[list[int]], list),
        (Annotated[int, "anno"], int),
        (Annotated[Annotated[list[int], "inner"], "outer"], list),
    ],
)
def test_get_origin(typ: type[Any], origin: type[Any]):
    assert _get_origin(typ) == origin


@pytest.mark.parametrize(
    "base,origin,spec",
    [
        (Parent, Child, [0]),
        (Parent, GrandChild, [0]),
        (Parent, Specific, [int]),
        (Parent, ExtraGeneric, [0]),
        (Parent, UnrelatedGeneric, [int]),
        (Parent, DisorderedGeneric, [1]),
        (Parent, AmbiguousChild, [(int, 0)])
    ],
)
def test_subclass_spec(base: type[Any], origin: type[Any], spec: list[int | type[Any]]):
    assert _subclass_spec(base, origin) == spec


@pytest.mark.parametrize(
    "base,actual,exp",
    [
        (Child, Parent[int], Child[int]),
        (Child, Parent[str], Child[str]),
        (GrandChild, Parent[str], GrandChild[str]),
        (Specific, Parent[int], Specific),
        (Specific, Parent[str], None),
        (DisorderedGeneric, Parent[int], DisorderedGeneric[T, int, V]),
        (ExtraGeneric, Parent[int], ExtraGeneric[int, V]),
        (UnrelatedGeneric, Parent[int], UnrelatedGeneric[U]),
        (UnrelatedGeneric, Parent[str], None),
    ],
)
def test_build_subclass(base: type[Any], actual: type[Any], exp: type[Any]):
    spec = _subclass_spec(_get_origin(actual), base)
    print(spec)
    assert _build_subclass(base, spec, actual) == exp


def test_constrained_child():
    cc = deserialize(ConstrainedParent[Any],
        {"type": "ConstrainedChild", "cc": "3.2", "cd": "42"}
    )
    assert cc.cc == pytest.approx(3.2)


def test_non_generic_child():
    ngc = deserialize(NonGenericParent,
        {"type": "NonGenericChild", "a": "42", "b": "3.14"}
    )
    assert ngc.a == 42
    assert ngc.b == pytest.approx(3.14)
