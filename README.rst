dotted_dict
=============

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
