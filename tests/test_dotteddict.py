import unittest

from dotted_dict import DottedDict


class dotteddictTests(unittest.TestCase):
    '''
    Test cases for the ``dotteddict`` class.
    '''
    def test_child_dictionary_types(self):
        dotted = DottedDict({'x': {'y': {'z': 5}}})

        self.assertEqual(type(dotted.x), DottedDict)
        self.assertEqual(type(dotted.x.y), DottedDict)

    def test_child_dictionary_types_accessor(self):
        dotted = DottedDict({'x': {'y': {'z': 5}}})

        self.assertEqual(type(dotted['x']), DottedDict)
        self.assertEqual(type(dotted['x']['y']), DottedDict)

    def test_children_equivalence(self):
        dotted = DottedDict({'x': {'y': {'z': 5}}})

        self.assertTrue(dotted.x is dotted['x'])
        self.assertTrue(dotted.x.y is dotted['x']['y'])

    def test_construction_without_data(self):
        dotted = DottedDict()
        self.assertTrue(isinstance(dotted, DottedDict))

    def test_delete(self):
        dotted = DottedDict({'foo': 1})
        del dotted.foo

        self.assertRaises(KeyError)

    def test_dotted_get(self):
        value = 'foo'
        data = {'color': {'blue': value}}

        dotted = DottedDict(data)

        self.assertEqual(dotted.get('color').get('blue'), value)

    def test_items_format_invocation(self):
        items = [('x', 1), ('y', 2), ('z', 3)]
        dotted = DottedDict(items)

        self.assertEquals(dotted.x, 1)
        self.assertEquals(dotted.y, 2)
        self.assertEquals(dotted.z, 3)

    def test_missing_attribute_error(self):
        dotted = DottedDict({'foo': None})

        with self.assertRaises(AttributeError):
            dotted.missing

    def test_none_value(self):
        value = None
        dotted = DottedDict({'foo': value})
        self.assertTrue(dotted.foo is value)

    def test_not_valid_identifier(self):
        # Contains invalid character
        with self.assertRaises(ValueError):
            DottedDict({'foo-bar': 1})
        with self.assertRaises(ValueError):
            DottedDict({'.foo': 1})
        # Reserved keyword
        with self.assertRaises(ValueError):
            DottedDict({'lambda': 1})

    def test_set_via_attrib(self):
        value = 42
        meaning = DottedDict()
        meaning.oflife = value

        self.assertEqual(meaning['oflife'], value)

    def test_setting_and_accessing(self):
        key = 'x'
        value = 5
        dotted = DottedDict({key: value})

        self.assertEqual(dotted[key], value)
        self.assertEqual(dotted.x, value)
        self.assertEqual(dotted.x, dotted[key])
