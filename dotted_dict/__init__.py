import keyword
import re


class DottedDict(dict):
    '''
    Override for the dict object to allow referencing of keys as attributes, i.e. dict.key
    '''
    def __init__(self, *args, **kwargs):
        super(DottedDict, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                self._parse_input(arg)

        if kwargs:
            self._parse_input(kwargs)

        self._handle_items_format()

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        # Do this to match python default behavior
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, key, value):
        if self._is_valid_identifier_(key):
            self.__setitem__(key, value)

    def __setitem__(self, key, value):
        if self._is_valid_identifier_(key):
            super(DottedDict, self).__setitem__(key, value)
            self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(DottedDict, self).__delitem__(key)
        del self.__dict__[key]

    def _handle_items_format(self):
        '''
        Handle input of items format (list of tuples).
        '''
        if self.items() and not self.__dict__.items():
            for key, value in self.items():
                self.__setitem__(key, value)

    def _is_valid_identifier_(self, identifier):
        '''
        Test the key name for valid identifier status as considered by the python lexer. Also
        check that the key name is not a python keyword.
        https://stackoverflow.com/questions/12700893/how-to-check-if-a-string-is-a-valid-python-identifier-including-keyword-check
        '''
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*$', identifier) and not keyword.iskeyword(identifier):
            return True
        raise ValueError('Key name is not a valid identifier or is reserved keyword.')

    def _parse_input(self, input_item):
        '''
        Parse the input item if dict into the dotted_dict constructor.
        '''
        for key, value in input_item.items():
            if isinstance(value, dict):
                value = DottedDict(**value)
            self[key] = value
