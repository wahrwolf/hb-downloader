from humble_authentication_exception import HumbleAuthenticationException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleCredentialException(HumbleAuthenticationException):
    """ Username and password don't match. """

    def __init__(self, *args, **kwargs):
        """
            Parameterized constructor for HumbleCredentialException.

            :param list args: (optional) Extra positional args to pass to the request.
            :param dict kwargs: (optional) Extra keyword args to pass to the request.
        """
        super(HumbleCredentialException, self).__init__(*args, **kwargs)
