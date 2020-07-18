

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

    @staticmethod
    def lookup_error_by_code(code, *args, **kwargs):
        '''
        Looks for a particular exception by a code representing the according error
        Arguments:
            code     : str      = error code defined in the Rapid API specification
            *args    : [?]      = additional arguments to be passed in an exception constructor
            **kwargs : {str: ?} = additional arguments to be passed in an exception constructor
        '''

        response_error = ResponseError.from_code(code)
        if response_error:
            return response_error

        validation_error = ValidationError.from_code(code, *args, **kwargs)
        if validation_error:
            return validation_error

        transaction_error = TransactionError.from_code(code, *args, **kwargs)
        if transaction_error:
            return transaction_error

        fraud_error = FraudError.from_code(code)
        if fraud_error:
            return fraud_error

        system_error = SysError.from_code(code)
        if system_error:
            return system_error

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

    @staticmethod
    def lookup_error_by_message(message, *args, **kwargs):
        '''
        Looks for a particular exception code by message
        Arguments:
            message  : str      = error message
            *args    : [?]      = additional arguments to be passed in an exception constructor
            **kwargs : {str: ?} = additional arguments to be passed in an exception constructor
        '''

        # Unlike within `lookup_error_by_code`, `UndocumentedError` comes first
        # as in the context of searching by message, it is the most likely candidate.
        error_classes = (ResponseError, ValidationError, TransactionError, FraudError, SysError)
        for error_class in error_classes:
            err = error_class.from_message(message, *args, **kwargs)
            if err:
                return err


class ResponseError(PaywayError):
    '''
    Represents errors defined in the specification as SDK Response Codes
    '''

    INDEX = {
        'S9990': 'Rapid endpoint not set or invalid',
        'S9901': 'Response is not JSON',
        'S9902': 'Empty response',
        'S9991': 'Rapid API key or password not set',
        'S9992': 'Error connecting to Rapid gateway',
        'S9993': 'Authentication error',
        'S9995': 'Error converting to or from JSON, invalid parameter',
        'S9996': 'Rapid gateway server error'
    }

    def __init__(self, code, *args, **kwargs):
        if code not in ResponseError.INDEX.keys():
            raise ValueError('Invalid error code: {}'.format(code))

        super(ResponseError, self).__init__(code, ResponseError.INDEX[code], *args, **kwargs)


class ValidationError(PaywayError):
    '''
    Represents errors defined in the specification as Validation Response Codes
    '''

    INDEX = {
        "V6000": "Validation error",
        "V6001": "Invalid CustomerIP",
        "V6002": "Invalid DeviceID",
        "V6003": "Invalid Request PartnerID",
        "V6004": "Invalid Request Method",
    }

    def __init__(self, code, *args, **kwargs):
        if code not in ValidationError.INDEX.keys():
            raise ValueError('Invalid error code: {}'.format(code))

        super(ValidationError, self).__init__(code, ValidationError.INDEX[code], *args, **kwargs)


class SysError(PaywayError):
    '''
    Represents errors defined in the specification as System Response Codes
    '''

    INDEX = {
        'S5000': 'System Error',
        'S5011': 'PayPal Connection Error',
        'S5012': 'PayPal Settings Error',
    }

    def __init__(self, code, *args, **kwargs):
        if code not in SysError.INDEX.keys():
            raise ValueError('Invalid error code: {}'.format(code))

        super(SysError, self).__init__(code, SysError.INDEX[code], *args, **kwargs)


class FraudError(PaywayError):
    '''
    Represents errors defined in the specification as Beagle Fraud Alerts and Beagle Fraud Alerts (Enterprise) Fraud Response Messages
    WARNING: A customer should not be informed their order has been flagged as possibly fraudulent. A generic failure message should be displayed instead.
    '''

    INDEX = {
        "F7000": "Undefined Fraud Error",
        "F7001": "Challenged Fraud",
    }

    def __init__(self, code, *args, **kwargs):
        if code not in FraudError.INDEX.keys():
            raise ValueError('Invalid error code: {}'.format(code))

        super(FraudError, self).__init__(code, FraudError.INDEX[code], *args, **kwargs)


class TransactionError(PaywayError):
    '''
    Represents errors defined in the specification as Transpaction Response Messages
    '''

    INDEX = {
        "A2000": "Transaction Approved Successful*",
        "A2008": "Honour With Identification Successful",
        "A2010": "Approved For Partial Amount Successful",
        "A2011": "Approved, VIP Successful",
        "A2016": "Approved, Update Track 3 Successful",
        "D4401": "Refer to Issuer Failed",
        "D4402": "Refer to Issuer, special Failed",
        "D4403": "No Merchant Failed",
    }

    def __init__(self, code, *args, **kwargs):
        if code not in TransactionError.INDEX.keys():
            raise ValueError('Invalid error code: {}'.format(code))

        super(TransactionError, self).__init__(code, TransactionError.INDEX[code], *args, **kwargs)
