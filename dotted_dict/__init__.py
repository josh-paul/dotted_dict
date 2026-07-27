"""Dotted access over dicts, for objectifying JSON and YAML you do not own.

No schema to declare and no model to keep in sync with someone else's API.
Conversion happens on write, so reads are plain attribute lookups.

Two behaviours, as two named classes rather than a flag:

    DottedDict
        Sanitises keys into valid Python identifiers, and refuses (rather than
        mangles) reserved words.

    PreserveKeysDottedDict
        Keeps keys exactly as given; some will then be reachable only via
        ``d['key']``.

Why values are stored twice:
    Every value lives both in the underlying ``dict`` and in ``self.__dict__``.
    These are two separate mappings, not one accessed two ways.

    That is deliberate, and it is the only reason ``d.items`` returns your data
    rather than the bound ``dict.items`` method: attribute lookup consults the
    instance ``__dict__`` before class attributes. JSON and YAML are full of
    keys named ``items``, ``keys``, ``values``, ``get`` and ``copy``, so this
    matters more here than it would elsewhere.

    The cost is that the two mappings can drift, and drift is exactly the bug
    this module used to have: ``dict.pop`` removed a key from one and left it
    in the other, so ``len(d)`` could report 0 while ``d['a']`` still returned
    a value.

    The fix is not to remove the second mapping. It is to make the set of write
    paths closed: every method that can mutate a dict is overridden below and
    routed through ``__setitem__`` or ``__delitem__``. The set feels open
    because Python never announces it, but it is finite. If a future release
    adds a mutator, it belongs in that block.
"""

import keyword
import re
import string

__all__ = ["BaseDottedDict", "DottedDict", "PreserveKeysDottedDict"]


class BaseDottedDict(dict):
    """Dotted attribute access over a dict, with no key policy.

    Subclasses customise three things and nothing else: ``_transform_key``
    (applied to every key on write, default identity), ``_child_type`` (the
    class nested dicts become), and ``_convert`` (how a value is converted on
    write).
    """

    # ------------------------------------------------------------------ hooks

    def _transform_key(self, key):
        """Apply the key policy on the way in. The default preserves the key.

        Override to impose a policy. Raising from here rejects the write.

        Args:
            key: The key as supplied by the caller.

        Returns:
            The key to store under.
        """
        return key

    def _child_type(self):
        """Return the class that nested dicts are converted into.

        Uses the runtime type rather than a hard-coded name so a subclass
        recurses into itself rather than degrading to its parent.

        Returns:
            type: The class to construct nested mappings as.
        """
        return type(self)

    def _convert(self, value):
        """Convert a value on the way in.

        Called from ``__setitem__``, which is the only write path, so
        construction, assignment, update and ``setdefault`` all convert
        identically.

        A value that is already an instance of ``_child_type()`` is stored as
        it stands rather than rebuilt. Converting it again would copy, which
        silently breaks shared references and self-reference, and costs a full
        walk on every reassignment of an existing structure.

        Args:
            value: Any value being stored. Plain dicts become ``_child_type()``
                instances; lists are walked so a list of dicts objectifies
                too; anything else passes through untouched.

        Returns:
            The converted value, or the original object when no conversion was
            needed.
        """
        if isinstance(value, self._child_type()):
            return value
        if isinstance(value, dict):
            return self._child_type()(value)
        if isinstance(value, list):
            return [self._convert(item) for item in value]
        return value

    # ------------------------------------------------------- the write paths
    #
    # Everything that can mutate the mapping funnels through __setitem__ or
    # __delitem__, so the dict and the attribute namespace cannot drift apart.
    # These overrides look redundant. They are not: dict's own versions write
    # to the dict alone and would leave the attribute namespace stale.

    def __setitem__(self, key, value):
        """Store a value, applying the key policy and converting the value.

        This is the single write path. Every other mutator routes here.
        """
        key = self._transform_key(key)
        value = self._convert(value)
        super().__setitem__(key, value)
        self.__dict__[key] = value

    def __delitem__(self, key):
        """Remove a key from both mappings.

        This is the single delete path.
        """
        super().__delitem__(key)
        self.__dict__.pop(key, None)

    def __setattr__(self, key, value):
        """Route attribute assignment through ``__setitem__``.

        Makes ``d.x = v`` and ``d['x'] = v`` the same operation, including key
        policy and value conversion.
        """
        self[key] = value

    def __delattr__(self, item):
        """Route attribute deletion through ``__delitem__``.

        Raises:
            AttributeError: If the key is absent, matching what callers expect
                from ``del d.x`` rather than leaking a KeyError.
        """
        try:
            del self[item]
        except KeyError:
            raise AttributeError(item) from None

    def update(self, *args, **kwargs):
        """Merge in new items, converting values and applying the key policy.

        Overridden because ``dict.update`` writes directly and would bypass
        both.

        Args:
            *args: Any mix of mappings and iterables of key/value pairs.
            **kwargs: Items given as keywords.
        """
        for arg in args:
            if hasattr(arg, "keys"):
                for key in arg:
                    self[key] = arg[key]
            else:
                for key, value in arg:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def setdefault(self, key, default=None):
        """Return the value for a key, inserting a converted default if absent.

        Overridden because ``dict.setdefault`` inserts without going through
        ``__setitem__``, so the default would be stored unconverted and the
        attribute namespace would not see it.

        Args:
            key: The key to look up.
            default: Value to insert when the key is missing. Converted on
                insert, so a dict default becomes a dotted instance.

        Returns:
            The existing value, or the newly inserted default.
        """
        key = self._transform_key(key)
        if key not in self:
            self[key] = default
        return self[key]

    def pop(self, key, *args):
        """Remove a key and return its value, clearing it from both mappings.

        Overridden because ``dict.pop`` removes from the dict alone. Without
        this, ``len(d)`` drops but ``d[key]`` still resolves.

        Args:
            key: The key to remove.
            *args: An optional default, as ``dict.pop`` accepts.

        Returns:
            The removed value, or the default when one was supplied.

        Raises:
            KeyError: If the key is absent and no default was given.
        """
        value = super().pop(key, *args)
        self.__dict__.pop(key, None)
        return value

    def popitem(self):
        """Remove and return one item, clearing it from both mappings.

        Returns:
            tuple: The removed ``(key, value)`` pair.
        """
        key, value = super().popitem()
        self.__dict__.pop(key, None)
        return key, value

    def clear(self):
        """Empty both mappings.

        Overridden because ``dict.clear`` alone would leave every value still
        reachable by attribute.
        """
        super().clear()
        self.__dict__.clear()

    def __ior__(self, other):
        """Merge in place (``d |= other``), routed through ``update`` so the
        incoming values are converted.

        Returns:
            BaseDottedDict: This instance.
        """
        self.update(other)
        return self

    def __or__(self, other):
        """Merge (``d | other``), returning this class rather than a plain dict.

        Returns:
            BaseDottedDict: A new instance with ``other`` merged over a copy.
        """
        merged = self.copy()
        merged.update(other)
        return merged

    def __ror__(self, other):
        """Merge with a plain mapping on the left (``other | d``).

        Returns:
            BaseDottedDict: A new instance, with values from this one winning.
        """
        merged = self._child_type()(other)
        merged.update(self)
        return merged

    @classmethod
    def fromkeys(cls, iterable, value=None):
        """Build an instance from keys, all sharing one value.

        Overridden so the result is this class with the key policy applied;
        ``dict.fromkeys`` would build the mapping without either.

        Args:
            iterable: The keys to create.
            value: The value assigned to every key.

        Returns:
            BaseDottedDict: A new instance of the calling class.
        """
        new = cls()
        for key in iterable:
            new[key] = value
        return new

    # -------------------------------------------------------- the read paths

    def __init__(self, *args, **kwargs):
        """Build from mappings, iterables of pairs, and keywords.

        Every item goes through ``update`` and therefore through the single
        write path, so construction and assignment behave identically.

        Args:
            *args: Any mix of mappings and iterables of key/value pairs.
            **kwargs: Items given as keywords.
        """
        super().__init__()
        for arg in args:
            self.update(arg)
        if kwargs:
            self.update(kwargs)

    def __getattr__(self, attr):
        """Resolve a missing attribute as a key.

        Only called when normal attribute lookup fails, which for data keys
        means the key is genuinely absent.

        Args:
            attr: The attribute name being looked up.

        Returns:
            The stored value.

        Raises:
            AttributeError: If the key is absent. Missing keys raise rather
                than autovivifying, so a typo fails loudly instead of quietly
                creating an empty node.
        """
        try:
            return self.__dict__[attr]
        except KeyError:
            raise AttributeError(attr) from None

    def __getitem__(self, key):
        """Read from the attribute namespace, which the write paths keep
        identical to the dict.

        Returns:
            The stored value.

        Raises:
            KeyError: If the key is absent.
        """
        return self.__dict__[key]

    def __repr__(self):
        """Wrap the dict repr in the class name, so nested values show type.

        Returns:
            str: The representation.
        """
        return f"{type(self).__name__}({super().__repr__()})"

    def copy(self):
        """Copy into this class rather than the plain dict ``dict.copy`` gives.

        Returns:
            BaseDottedDict: A new instance; nested values are re-converted by
            the write path.
        """
        return type(self)(self)

    def to_dict(self, _seen=None):
        """Recursively convert back to plain dicts, including inside lists.

        Args:
            _seen: Internal. Maps object ids to their in-progress conversions
                so a structure referring to itself, at any depth, yields the
                same plain dict rather than recursing forever.

        Returns:
            dict: Plain dicts and lists all the way down.
        """
        if _seen is None:
            _seen = {}
        if id(self) in _seen:
            return _seen[id(self)]

        out = {}
        _seen[id(self)] = out
        for key, value in self.items():
            out[key] = _unconvert(value, _seen)
        return out


def _unconvert(value, seen):
    """Unwrap a value for ``to_dict``: instances recurse, lists are walked.

    Args:
        value: The value to unwrap.
        seen: The cycle map from ``to_dict``, carried through so shared or
            circular references converge on one object.

    Returns:
        The value as plain Python types.
    """
    if isinstance(value, BaseDottedDict):
        return value.to_dict(seen)
    if isinstance(value, list):
        return [_unconvert(item, seen) for item in value]
    return value


class PreserveKeysDottedDict(BaseDottedDict):
    """Keeps keys exactly as supplied.

    Keys that are not valid Python identifiers are still stored, but are
    reachable only via ``d['key']``, not ``d.key``. Use this when the exact
    keys matter more than attribute access, such as round-tripping a document
    you did not author.

    The class body is empty because preserving keys is the base behaviour. It
    exists as a name so the choice is explicit at the call site, rather than a
    boolean argument that can be passed wrongly.
    """


class DottedDict(BaseDottedDict):
    """Sanitises keys into valid Python identifiers so attribute access works.

    Spaces and invalid characters become underscores, and a leading digit is
    prefixed with one. Reserved words are refused rather than mangled, because
    silently renaming ``class`` loses data in a way the caller cannot predict.
    """

    _IDENTIFIER = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")
    _ALLOWED = frozenset(string.ascii_letters + string.digits + "_")

    def _transform_key(self, key):
        """Return a key usable as an attribute.

        Valid identifiers pass through untouched, so the common case costs one
        regex match and nothing else.

        Args:
            key: The key as supplied by the caller.

        Returns:
            The original key, or a sanitised version of it.

        Raises:
            ValueError: If the key is a Python reserved word. Refused rather
                than renamed, since any replacement would be unpredictable to
                the caller.
        """
        if self._is_valid_identifier_(key):
            return key
        if keyword.iskeyword(key):
            raise ValueError(f'Key "{key}" is a reserved keyword.')
        return self._make_safe_(key)

    def _is_valid_identifier_(self, identifier):
        """Report whether a key is usable as an attribute.

        Args:
            identifier: The key to test.

        Returns:
            bool: True when it matches the lexer's identifier rule and is not
            a Python keyword.
        """
        return bool(self._IDENTIFIER.match(str(identifier))) and not keyword.iskeyword(identifier)

    def _make_safe_(self, key):
        """Rewrite a key into a valid identifier.

        Anything that cannot appear in an identifier becomes ``_``, and a
        leading digit is prefixed with one.

        Note:
            This can collide. ``"a b"`` and ``"a-b"`` both become ``"a_b"``
            and the later write wins. Use ``PreserveKeysDottedDict`` when the
            exact keys matter more than attribute access.

        Args:
            key: The key to rewrite.

        Returns:
            str: A valid Python identifier.
        """
        key = str(key)
        key = "".join(char if char in self._ALLOWED else "_" for char in key)
        if key and key[0].isdigit():
            key = f"_{key}"
        return key
