from scanspec.core import discriminated_union_of_subclasses, _get_origin, _subclass_spec, _build_subclass
from pydantic import TypeAdapter
import pytest
from pydantic.dataclasses import dataclass
from typing import Generic, TypeVar, Annotated, Any

T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')

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

def test_child():
    ch = TypeAdapter(Parent[int]).validate_python({'type': 'Child', 'a': '42'})
    assert ch.a == 42

    ch = TypeAdapter(Parent[str]).validate_python({'type': 'Child', 'a': '42'})
    assert ch.a == '42'

def test_specific():
    ch = TypeAdapter(Parent[int]).validate_python({'type': 'Specific', 'b': '42'})
    assert ch.b == 42

    with pytest.raises(Exception):
        ch = TypeAdapter(Parent[str]).validate_python({'type': 'Specific', 'b': '42'})
        print(ch)

def test_extra_generic():
    ch = TypeAdapter(Parent[int]).validate_python({'type': 'ExtraGeneric', 'c': '42', 'd': 'foo'})
    assert ch.c == 42
    assert ch.d == 'foo'

def test_unrelated_generic():
    ch = TypeAdapter(Parent[int]).validate_python({'type': 'UnrelatedGeneric', 'e': '42', 'f': 'foo'})
    assert ch.e == 42
    assert ch.f == 'foo'

    with pytest.raises(Exception):
        ch = TypeAdapter(Parent[str]).validate_python({'type': 'UnrelatedGeneric', 'e': '42', 'f': 'foo'})

def test_disordered_generic():
    ch = TypeAdapter(Parent[int]).validate_python({'type': 'DisorderedGeneric', 'g': [1,2,3], 'h': '42', 'i': {'arbitrary': 'map'}})
    assert ch.g == [1,2,3]
    assert ch.h == 42
    assert ch.i == {'arbitrary': 'map'}

@pytest.mark.parametrize('typ,origin', [
    (int, int),
    (list[int], list),
    (list[list[int]], list),
    (Annotated[int, "anno"], int),
    (Annotated[Annotated[list[int], "inner"], "outer"], list)
    ])
def test_get_origin(typ: type[Any], origin: type[Any]):
    assert _get_origin(typ) == origin

@pytest.mark.parametrize('base,origin,spec', [
    (Parent, Child, [0]),
    (Parent, GrandChild, [0]),
    (Parent, Specific, [int]),
    (Parent, ExtraGeneric, [0]),
    (Parent, UnrelatedGeneric, [int]),
    (Parent, DisorderedGeneric, [1])
    ])
def test_subclass_spec(base: type[Any], origin: type[Any], spec: list[int|type[Any]]):
    print()
    assert _subclass_spec(base, origin) == spec

@pytest.mark.parametrize('base,actual,exp', [
    (Child, Parent[int], Child[int]),
    (Child, Parent[str], Child[str]),
    (GrandChild, Parent[str], GrandChild[str]),
    (Specific, Parent[int], Specific),
    (Specific, Parent[str], None),
    (DisorderedGeneric, Parent[int], DisorderedGeneric[T, int, V]),
    (ExtraGeneric, Parent[int], ExtraGeneric[int, V]),
    (UnrelatedGeneric, Parent[int], UnrelatedGeneric[U]),
    (UnrelatedGeneric, Parent[str], None),
    ])
def test_build_subclass(base: type[Any], actual: type[Any], exp: type[Any]):
    spec = _subclass_spec(_get_origin(actual), base)
    print(spec)
    assert _build_subclass(base, spec, actual) == exp
