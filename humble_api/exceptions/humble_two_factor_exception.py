from humble_authentication_exception import HumbleAuthenticationException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleTwoFactorException(HumbleAuthenticationException):
    """ The one time password was invalid. """

    def __init__(self, *args, **kwargs):
        """
            Parameterized constructor for HumbleTwoFactorException.

            :param list args: (optional) Extra positional args to pass to the request.
            :param dict kwargs: (optional) Extra keyword args to pass to the request.
        """
        super(HumbleTwoFactorException, self).__init__(*args, **kwargs)

