

class PaywayError(Exception):
    INDEX = {}
    REVERSE_INDEX = None

    _code = None
    _message = None

    def __init__(self, code, message, *args, **kwargs):
        '''
        Arguments:
            code            : str = PayWay API response/error code
            message         : str = appropriate message
            response_struct : ?   = Object representing a response which caused the error
            response_string : str = String representing a response which caused the error
        '''

        super(PaywayError, self).__init__(*args, **kwargs)

        self._code = code
        self._message = '{}: {}'.format(code, message).encode('utf-8')

    def __bytes__(self):
        return self._message

    def __unicode__(self):
        try:
            return unicode(self.__bytes__())
        except NameError:
            return str(self.__bytes__(), 'utf-8')

    def __str__(self):
        return self.__bytes__().decode('utf-8')

    def __repr__(self):
        return self.__unicode__()

    @classmethod
    def from_code(cls, code, *args, **kwargs):
        '''
        Create an error object from code
        '''

        if code in cls.INDEX:
            return cls(code, *args, **kwargs)

        return None

    @classmethod
    def from_message(cls, message, *args, **kwargs):
        '''
        Create an error object from message
        '''

        if cls.REVERSE_INDEX is None:
            cls.REVERSE_INDEX = {msg: code for code, msg in cls.INDEX.items()}

        code = cls.REVERSE_INDEX.get(message, None)
        if code:
            return cls(code, *args, **kwargs)

        return None
