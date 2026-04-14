import pytest
from frozen_dict import FrozenDict
from collections import Counter


class TestFrozenDictCreation:
    def test_empty_creation(self):
        fd = FrozenDict()
        assert dict(fd) == {}

    def test_creation_with_dict(self):
        fd = FrozenDict({"a": 1, "b": 2})
        assert fd["a"] == 1
        assert fd["b"] == 2

    def test_creation_from_string(self):
        fd = FrozenDict.from_string("hello")
        assert fd["h"] == 1
        assert fd["e"] == 1
        assert fd["l"] == 2
        assert fd["o"] == 1

    def test_creation_from_string_empty(self):
        fd = FrozenDict.from_string("")
        assert len(fd) == 0


class TestFrozenDictImmutability:
    def test_cannot_setitem(self):
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            fd["b"] = 2

    def test_cannot_delitem(self):
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            del fd["a"]

    def test_cannot_clear(self):
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            fd.clear()

    def test_cannot_pop(self):
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            fd.pop("a")

    def test_cannot_popitem(self):
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            fd.popitem()

    def test_cannot_setdefault(self):
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            fd.setdefault("b", 2)

    def test_cannot_update(self):
        fd = FrozenDict({"a": 1})
        with pytest.raises(TypeError):
            fd.update({"b": 2})


class TestFrozenDictHash:
    def test_hash_same_contents(self):
        fd1 = FrozenDict.from_string("hello")
        fd2 = FrozenDict.from_string("hello")
        assert hash(fd1) == hash(fd2)

    def test_hash_different_contents(self):
        fd1 = FrozenDict.from_string("hello")
        fd2 = FrozenDict.from_string("world")
        assert hash(fd1) != hash(fd2)

    def test_hash_consistent(self):
        fd = FrozenDict.from_string("hello")
        h1 = hash(fd)
        h2 = hash(fd)
        assert h1 == h2

    def test_can_be_used_as_dict_key(self):
        fd1 = FrozenDict.from_string("hello")
        fd2 = FrozenDict.from_string("hello")
        d = {fd1: "value"}
        assert d[fd2] == "value"


class TestFrozenDictRepr:
    def test_repr(self):
        fd = FrozenDict({"a": 1})
        assert "FrozenDict" in repr(fd)
        assert "a" in repr(fd)
