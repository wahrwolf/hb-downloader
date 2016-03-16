from humble_authentication_exception import HumbleAuthenticationException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleCaptchaException(HumbleAuthenticationException):
    """ The CAPTCHA response was invalid. """

    def __init__(self, *args, **kwargs):
        """
            Parameterized constructor for the HumbleCaptchaException.

            :param list args: (optional) Extra positional args to pass to the request.
            :param dict kwargs: (optional) Extra keyword args to pass to the request.
        """
        super(HumbleCaptchaException, self).__init__(*args, **kwargs)
