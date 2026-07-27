"""Tests for the write-path closure and the behaviour it protects.

The original implementation stored every value twice -- once in the dict and
once in the instance attribute namespace -- but overrode only some of the
methods that can mutate a dict. The rest wrote to one store and left the other
stale, so ``len(d)`` could report 0 while ``d['a']`` still returned a value.

These tests pin each of those paths, and pin the closure itself: if a future
Python grows a new dict mutator, ``test_dict_public_surface_is_known`` fails and
the write-path block gets revisited.
"""

import json
import unittest

from dotted_dict import BaseDottedDict, DottedDict, PreserveKeysDottedDict


class WritePathClosureTests(unittest.TestCase):
    """Every way to mutate a dict must route through the overridden paths."""

    # Methods on dict that can change its contents. Each must be overridden so
    # the attribute namespace is kept in step.
    MUTATORS = frozenset(
        {
            "__setitem__",
            "__delitem__",
            "__ior__",
            "clear",
            "pop",
            "popitem",
            "setdefault",
            "update",
            "fromkeys",
        }
    )

    # dict's public (non-dunder) surface. Stable for many releases. A new entry
    # here means Python grew a method, and the only question that matters is
    # whether it can mutate -- if so it belongs in MUTATORS and needs an
    # override. This test exists to force that question rather than let a new
    # mutator silently reopen the drift bug.
    PUBLIC_SURFACE = frozenset(
        {
            "clear",
            "copy",
            "fromkeys",
            "get",
            "items",
            "keys",
            "pop",
            "popitem",
            "setdefault",
            "update",
            "values",
        }
    )

    def test_every_known_mutator_is_overridden(self):
        for name in sorted(self.MUTATORS):
            with self.subTest(method=name):
                self.assertIn(
                    name,
                    vars(BaseDottedDict),
                    f"{name} can mutate a dict but is not overridden; the two stores will drift",
                )

    def test_dict_public_surface_is_known(self):
        actual = {name for name in dir(dict) if not name.startswith("_")}
        self.assertEqual(
            actual,
            self.PUBLIC_SURFACE,
            "dict's public surface changed. If the new method can mutate, add "
            "an override in the write-path block and list it in MUTATORS.",
        )


class DesyncRegressionTests(unittest.TestCase):
    """Each of these silently returned stale data before the closure existed."""

    def assert_stores_agree(self, dotted):
        self.assertEqual(
            dict.copy(dotted),
            dict(dotted.__dict__),
            "the dict and the attribute namespace have drifted",
        )

    def test_pop_clears_both_stores(self):
        dotted = DottedDict({"a": 1, "b": 2})
        self.assertEqual(dotted.pop("a"), 1)
        self.assert_stores_agree(dotted)
        self.assertEqual(len(dotted), 1)
        with self.assertRaises(KeyError):
            dotted["a"]
        with self.assertRaises(AttributeError):
            dotted.a

    def test_pop_with_default_does_not_raise(self):
        dotted = DottedDict({"a": 1})
        self.assertIsNone(dotted.pop("missing", None))
        self.assert_stores_agree(dotted)

    def test_pop_missing_without_default_raises(self):
        with self.assertRaises(KeyError):
            DottedDict().pop("missing")

    def test_popitem_clears_both_stores(self):
        dotted = DottedDict({"a": 1})
        key, value = dotted.popitem()
        self.assertEqual((key, value), ("a", 1))
        self.assert_stores_agree(dotted)
        self.assertEqual(len(dotted), 0)

    def test_clear_clears_both_stores(self):
        dotted = DottedDict({"a": 1, "b": 2})
        dotted.clear()
        self.assert_stores_agree(dotted)
        self.assertEqual(len(dotted), 0)
        with self.assertRaises(AttributeError):
            dotted.a

    def test_setdefault_writes_to_both_stores(self):
        dotted = DottedDict()
        dotted.setdefault("a", 1)
        self.assert_stores_agree(dotted)
        self.assertEqual(dotted.a, 1)

    def test_setdefault_returns_existing_without_replacing(self):
        dotted = DottedDict({"a": 1})
        self.assertEqual(dotted.setdefault("a", 99), 1)
        self.assertEqual(dotted.a, 1)

    def test_delitem_clears_both_stores(self):
        dotted = DottedDict({"a": 1})
        del dotted["a"]
        self.assert_stores_agree(dotted)

    def test_ior_merges_and_converts(self):
        dotted = DottedDict({"a": 1})
        dotted |= {"b": {"c": 2}}
        self.assert_stores_agree(dotted)
        self.assertIsInstance(dotted.b, DottedDict)
        self.assertEqual(dotted.b.c, 2)


class ConversionOnWriteTests(unittest.TestCase):
    """Assignment must convert, not only construction."""

    def test_attribute_assignment_converts(self):
        dotted = DottedDict()
        dotted.foo = {"bar": {"baz": 1}}
        self.assertIsInstance(dotted.foo, DottedDict)
        self.assertEqual(dotted.foo.bar.baz, 1)

    def test_item_assignment_converts(self):
        dotted = DottedDict()
        dotted["foo"] = {"bar": 1}
        self.assertIsInstance(dotted["foo"], DottedDict)
        self.assertEqual(dotted.foo.bar, 1)

    def test_assignment_converts_dicts_inside_lists(self):
        dotted = DottedDict()
        dotted.rows = [{"n": 1}, {"n": 2}, "not a dict"]
        self.assertIsInstance(dotted.rows[0], DottedDict)
        self.assertEqual(dotted.rows[1].n, 2)
        self.assertEqual(dotted.rows[2], "not a dict")

    def test_setdefault_converts(self):
        dotted = DottedDict()
        dotted.setdefault("cfg", {"host": "localhost"})
        self.assertIsInstance(dotted.cfg, DottedDict)
        self.assertEqual(dotted.cfg.host, "localhost")

    def test_fromkeys_applies_class_and_policy(self):
        dotted = DottedDict.fromkeys(["a b", "c"], {"n": 1})
        self.assertIsInstance(dotted, DottedDict)
        self.assertEqual(dotted.a_b.n, 1)

    def test_child_type_follows_the_subclass(self):
        preserved = PreserveKeysDottedDict({"outer": {"a b": 1}})
        self.assertIsInstance(preserved.outer, PreserveKeysDottedDict)
        self.assertEqual(preserved.outer["a b"], 1)


class BehaviourPreservedTests(unittest.TestCase):
    """Properties that must survive the refactor."""

    def test_data_shadows_dict_methods(self):
        # The whole reason values live in the attribute namespace: JSON is full
        # of keys named items/keys/values/get.
        dotted = DottedDict({"items": [1, 2], "keys": "k", "get": "g"})
        self.assertEqual(dotted.items, [1, 2])
        self.assertEqual(dotted.keys, "k")
        self.assertEqual(dotted.get, "g")

    def test_is_still_a_real_dict(self):
        dotted = DottedDict({"a": {"b": 1}})
        self.assertIsInstance(dotted, dict)
        self.assertEqual(json.dumps(dotted), '{"a": {"b": 1}}')

    def test_missing_key_raises_rather_than_autovivifying(self):
        dotted = DottedDict({"user_name": "x"})
        with self.assertRaises(AttributeError):
            dotted.usre_name
        self.assertEqual(len(dotted), 1, "a failed read must not create a key")

    def test_reserved_keyword_is_refused_not_mangled(self):
        with self.assertRaises(ValueError):
            DottedDict({"class": 1})

    def test_to_dict_is_cycle_safe(self):
        dotted = DottedDict({"a": 1})
        dotted.self_ref = dotted
        plain = dotted.to_dict()
        self.assertIs(plain["self_ref"], plain)
        self.assertEqual(plain["a"], 1)

    def test_to_dict_unwraps_inside_lists(self):
        dotted = DottedDict({"rows": [{"n": 1}]})
        plain = dotted.to_dict()
        self.assertIs(type(plain["rows"][0]), dict)

    def test_copy_returns_the_same_class(self):
        for cls in (DottedDict, PreserveKeysDottedDict):
            with self.subTest(cls=cls.__name__):
                self.assertIsInstance(cls({"a": 1}).copy(), cls)


if __name__ == "__main__":
    unittest.main()
