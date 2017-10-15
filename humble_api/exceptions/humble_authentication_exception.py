from .humble_response_exception import HumbleResponseException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


class HumbleAuthenticationException(HumbleResponseException):
    """
        An unspecified authentication failure occurred.

        captcha_required:  Whether CAPTCHA is resolution is required for login.
        authy_required:  Whether the Authy token is required for login.
    """

    def __init__(self, *args, **kwargs):
        """
            Parameterized constructor for the HumbleAuthenticationException.

            :param list args: (optional) Extra positional args to pass to the request.
            :param dict kwargs: (optional) Extra keyword args to pass to the request.
        """
        self.captcha_required = kwargs.pop("captcha_required", None)
        self.authy_required = kwargs.pop("authy_required", None)

        super(HumbleAuthenticationException, self).__init__(*args, **kwargs)
