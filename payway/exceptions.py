

class PaywayError(Exception):
    _code = None
    _message = None

    def __init__(self, code, message, *args, **kwargs):
        """
        code            : str = PayWay API response/error code
        message         : str = appropriate message
        """

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
