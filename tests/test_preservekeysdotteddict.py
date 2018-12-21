import unittest

from dotted_dict import DottedDict, PreserveKeysDottedDict


class dotteddictTests(unittest.TestCase):
    '''
    Test cases for the ``dotteddict`` class.
    '''
    def test_child_dictionary_types(self):
        dotted = PreserveKeysDottedDict({'x': {'y': {'z': 5}}})

        self.assertEqual(type(dotted.x), PreserveKeysDottedDict)
        self.assertEqual(type(dotted.x.y), PreserveKeysDottedDict)

    def test_child_dictionary_types_accessor(self):
        dotted = PreserveKeysDottedDict({'x': {'y': {'z': 5}}})

        self.assertEqual(type(dotted['x']), PreserveKeysDottedDict)
        self.assertEqual(type(dotted['x']['y']), PreserveKeysDottedDict)

    def test_children_equivalence(self):
        dotted = PreserveKeysDottedDict({'x': {'y': {'z': 5}}})

        self.assertTrue(dotted.x is dotted['x'])
        self.assertTrue(dotted.x.y is dotted['x']['y'])

    def test_construction_without_data(self):
        dotted = PreserveKeysDottedDict()
        self.assertTrue(isinstance(dotted, PreserveKeysDottedDict))

    def test_copy(self):
        my_dict = PreserveKeysDottedDict({'my key two': {'b': 'c', 1: 2}})
        dotted = my_dict.copy()
        self.assertEquals(my_dict, dotted)

    def test_delete(self):
        dotted = PreserveKeysDottedDict({'foo': 1})
        del dotted.foo

        self.assertRaises(KeyError)

    def test_dotted_get(self):
        value = 'foo'
        data = {'color': {'blue': value}}

        dotted = PreserveKeysDottedDict(data)

        self.assertEqual(dotted.get('color').get('blue'), value)

    def test_items_format_invocation(self):
        items = [('x', 1), ('y', 2), ('z', 3)]
        dotted = PreserveKeysDottedDict(items)

        self.assertEquals(dotted.x, 1)
        self.assertEquals(dotted.y, 2)
        self.assertEquals(dotted.z, 3)

    def test_missing_attribute_error(self):
        dotted = PreserveKeysDottedDict({'foo': None})

        with self.assertRaises(AttributeError):
            dotted.missing

    def test_none_value(self):
        value = None
        dotted = PreserveKeysDottedDict({'foo': value})
        self.assertTrue(dotted.foo is value)

    def test_not_valid_identifier(self):
        dotted = PreserveKeysDottedDict({'foo-bar': 1, '.foo': 1, 'foo baz': 1, 1: 2})
        self.assertTrue(dotted['foo-bar'], 1)
        self.assertTrue(dotted['.foo'], 1)
        self.assertTrue(dotted['foo baz'], 1)
        self.assertTrue(dotted[1], 2)
        # Reserved keyword
        # with self.assertRaises(ValueError):
        #     DottedDict({'lambda': 1})

    def test_repr(self):
        dotted = PreserveKeysDottedDict({'foo-bar': 1, '.foo': 1, 'foo baz': 1, 1: 2})
        assert eval(repr(dotted)) == dotted

    def test_set_via_attrib(self):
        value = 42
        meaning = PreserveKeysDottedDict()
        meaning.oflife = value

        self.assertEqual(meaning['oflife'], value)

    def test_setting_and_accessing(self):
        key = 'x'
        value = 5
        dotted = PreserveKeysDottedDict({key: value})

        self.assertEqual(dotted[key], value)
        self.assertEqual(dotted.x, value)
        self.assertEqual(dotted.x, dotted[key])

    def test_to_dict(self):
        dotted = PreserveKeysDottedDict(
            PreserveKeysDottedDict({'a': 'b', 'c': {'d': 'e'}, 'f': [{'g': 'h'}, 1]})
        )
        my_dict = dotted.to_dict()
        self.assertEquals(dotted, my_dict)
        self.assertEqual(type(dotted), PreserveKeysDottedDict)
        self.assertEqual(type(dotted.f[0]), PreserveKeysDottedDict)
        self.assertEqual(type(my_dict), dict)
        self.assertEqual(type(my_dict['f'][0]), dict)
