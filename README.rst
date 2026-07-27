dotted_dict
===========

.. image:: https://github.com/josh-paul/dotted_dict/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/josh-paul/dotted_dict/actions/workflows/ci.yml
    :alt: CI

.. image:: https://img.shields.io/pypi/v/dotted_dict.svg
    :target: https://pypi.org/project/dotted_dict/
    :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/dotted_dict.svg
    :target: https://pypi.org/project/dotted_dict/
    :alt: Python versions

Dotted access over dicts, for objectifying JSON and YAML you do not own.

No schema to declare and no model to keep in sync with someone else's API.
Zero dependencies, one file. Conversion happens on write, so reads are plain
attribute lookups.

.. code-block:: python

    >>> import json
    >>> from dotted_dict import DottedDict

    >>> document = '{"database": {"replicas": [{"host": "db-1.internal"}]}}'
    >>> config = DottedDict(json.loads(document))
    >>> config.database.replicas[0].host
    'db-1.internal'

In practice that is ``DottedDict(json.load(handle))`` or
``DottedDict(yaml.safe_load(handle))``.

Declaring a model for a document you did not author means maintaining a mirror
of a contract that changes without telling you, and breaking on fields you
never asked about. This does not do that. It takes what arrived.

Install
-------

.. code-block:: shell

    pip install dotted_dict

Requires Python 3.9 or later. No runtime dependencies.

Usage
-----

Keys are reachable as attributes, and attributes are keys. They are the same
operation.

.. code-block:: python

    >>> from dotted_dict import DottedDict

    >>> example = DottedDict()
    >>> example["foo"] = 1
    >>> example.foo
    1

    >>> example.bar = 2
    >>> example
    DottedDict({'foo': 1, 'bar': 2})

    >>> del example["foo"]
    >>> del example.bar
    >>> example
    DottedDict({})

Nested dicts, and dicts inside lists, are converted as they are stored --
whether they arrive through the constructor, an assignment, an update, or
``setdefault``.

.. code-block:: python

    >>> d = DottedDict()
    >>> d.service = {"ports": [{"name": "http", "number": 80}]}
    >>> d.service.ports[0].number
    80

A value that is already the right type is stored as-is rather than copied, so
shared references survive.

Convert back to plain dicts with ``to_dict()``, which is cycle-safe at any
depth.

.. code-block:: python

    >>> d.to_dict()
    {'service': {'ports': [{'name': 'http', 'number': 80}]}}

It remains a real ``dict``, so anything expecting one keeps working.

.. code-block:: python

    >>> isinstance(d, dict)
    True
    >>> json.dumps(d)
    '{"service": {"ports": [{"name": "http", "number": 80}]}}'

Two classes, not a flag
-----------------------

**DottedDict** sanitises keys into valid Python identifiers so attribute
access works. A valid key matches ``[a-zA-Z_][a-zA-Z0-9_]*$``. Spaces and
invalid characters become ``_``, and a leading digit gets a ``_`` prefix.

.. code-block:: python

    >>> DottedDict({"My fun key": 1, "John's": 1, "Mr. Man": 1})
    DottedDict({'My_fun_key': 1, 'John_s': 1, 'Mr__Man': 1})

    >>> DottedDict({1: 2})
    DottedDict({'_1': 2})

Reserved words are **refused rather than renamed**, because any substitute
would be unpredictable to you.

.. code-block:: python

    >>> DottedDict({"class": 1})
    Traceback (most recent call last):
    ValueError: Key "class" is a reserved keyword.

Sanitising can collide: ``"a b"`` and ``"a-b"`` both become ``"a_b"``, and the
later write wins. When the exact keys matter more than attribute access, use
the other class.

**PreserveKeysDottedDict** stores keys exactly as given. Keys that are not
valid identifiers are still there, reachable via ``d["key"]``.

.. code-block:: python

    >>> from dotted_dict import PreserveKeysDottedDict

    >>> d = PreserveKeysDottedDict({"content-type": "application/json"})
    >>> d["content-type"]
    'application/json'

Two named classes rather than one class with a boolean, so the choice is
visible at the call site and cannot be passed wrongly.

Missing keys raise
------------------

A key that is not there raises, rather than creating an empty node. A typo
should fail, not quietly succeed.

.. code-block:: python

    >>> d = DottedDict({"user_name": "josh"})
    >>> d.usre_name
    Traceback (most recent call last):
    AttributeError: usre_name

Subclassing
-----------

``BaseDottedDict`` provides the behaviour with no key policy. Subclasses
customise three hooks and nothing else:

``_transform_key(key)``
    Applied to every key on write. Default preserves it. Raising rejects the
    write.

``_child_type()``
    The class nested dicts become. Defaults to the runtime type, so a subclass
    recurses into itself.

``_convert(value)``
    How a value is converted on write.

Every mutating method routes through ``__setitem__``, so a hook applies
uniformly no matter how the data arrived.

Upgrading from 1.x
------------------

**Fixed:** ``pop``, ``popitem``, ``setdefault`` and ``clear`` previously
mutated only one of the two internal stores, so a popped key could still be
readable and ``len()`` could disagree with what was reachable.

**Changed:** assignment now converts. ``d.foo = {"bar": 1}`` yields a
``DottedDict``, where 1.x stored a plain ``dict``. If you relied on getting a
plain dict back from an assignment, call ``to_dict()`` on it.

**Added:** ``BaseDottedDict`` is public, ``to_dict()`` is cycle-safe at any
depth rather than only for direct self-reference, and ``|`` / ``|=`` /
``fromkeys`` return the correct class.

**Dropped:** Python 2 and Python 3.8 and earlier.

License
-------

Apache-2.0.
