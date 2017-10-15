from .humble_authentication_exception import HumbleAuthenticationException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleTwoFactorException(HumbleAuthenticationException):
    """ The one time password was invalid. """
    pass
