from humble_authentication_exception import HumbleAuthenticationException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleCaptchaException(HumbleAuthenticationException):
    """ The CAPTCHA response was invalid. """
    pass