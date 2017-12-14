dotted_dict
=============

.. image:: https://travis-ci.org/josh-paul/dotted_dict.svg?branch=master
    :target: https://travis-ci.org/josh-paul/dotted_dict
    :alt: Travis CI Build

.. image:: http://codecov.io/github/josh-paul/dotted_dict/coverage.svg?branch=master
    :target: http://codecov.io/github/josh-paul/dotted_dict?branch=master
    :alt: Coverage

.. image:: https://api.codeclimate.com/v1/badges/a5bdee8792e6a6379df1/maintainability
   :target: https://codeclimate.com/github/josh-paul/dotted_dict/maintainability
   :alt: Code Climate Maintainability

A light weight extension of the default python dict object. This allows for the use of key names as 
object attributes. 

Simple usage
::

    In [1]: from dotted_dict import DottedDict

    In [2]: example = DottedDict()

    In [3]: example['foo'] = 1

    In [4]: example.foo
    Out[4]: 1

    In [5]: example.bar = 2

    In [6]: example
    Out[6]: {'bar': 2, 'foo': 1}

    In [7]: del example['foo']

    In [8]: del example.bar

    In [9]: example
    Out[9]: {}


Also allows passing in of values in same manner as normal dict objects.
::

    In [10]: example = DottedDict({'foo': 1, 'bar': 2})

    In [11]: example
    Out[11]: {'bar': 2, 'foo': 1}

Issues with invalid characters. A valid key name in the scope of this library must conform to the
following regex :code:`[a-zA-Z_][a-zA-Z0-9_]*$`. In the case where your key name does not conform,
the library will mutate your key to a safe format. Spaces and invalid characters are replaced with
_. In the case of the key beginning with an int, a leading _ is added.
::

    In [12]: DottedDict({'My fun key': 1, 'John\'s': 1, 'Mr. Man': 1})
    Out[12]: {'John_s': 1, 'Mr__Man': 1, 'My_fun_key': 1}

    In [13]: DottedDict({1: 2})
    Out[13]: {'_1': 2}