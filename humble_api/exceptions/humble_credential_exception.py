from .humble_authentication_exception import HumbleAuthenticationException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleCredentialException(HumbleAuthenticationException):
    """ Username and password don't match. """
    pass
