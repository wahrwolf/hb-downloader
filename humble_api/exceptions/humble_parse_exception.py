from humble_response_exception import HumbleResponseException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleParseException(HumbleResponseException):
    """ An error occurred while parsing the response. """

    def __init__(self, *args, **kwargs):
        """
            Parameterized constructor for HumbleParseException.

            :param list args: (optional) Extra positional args to pass to the request.
            :param dict kwargs: (optional) Extra keyword args to pass to the request.
        """
        super(HumbleParseException, self).__init__(*args, **kwargs)
