from humblebundle.exceptions import *
from humblebundle.models import *
import configuration
import cookielib
import itertools

"""
The Humble Bundle API client
"""

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"

__all__ = ["HumbleApi"]


class HumbleApi(object):
    """
        The Humble Bundle API is not stateless, it stores an authentication token as a cookie named _simpleauth_sess

        The Requests.Session handles storing the auth token. To load some persisted cookies simply set session.cookies
        after initialization.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.cookies = cookielib.LWPCookieJar(configuration.cookie_filename)
        self.session.cookies.load()
        self.session.headers.update(configuration.default_headers)
        self.session.params.update(configuration.default_params)

    def check_login(self):
        """
            Checks to see if we have a valid session cookie by attempting to retrieve the orders page.
            If we get a HumbleAuthenticationException then we need to log in to the system again.
            Otherwise we're good to go.

            :return: True if the _simpleauth_sess cookie has been set, False if not.
        """
        try:
            gamekeys = self.get_gamekeys()
            if len(gamekeys) > 0:
                return True
            else:
                return False
        except HumbleAuthenticationException:
            return False

    def login(self, *args, **kwargs):
        """
            Login to the Humble Bundle API. The response sets the _simpleauth_sess cookie which is stored in the session
            automatically.

            :param list args: (optional) Extra positional args to pass to the request
            :param dict kwargs: (optional) Extra keyword args to pass to the request. If a data dict is supplied a key
                                collision with any of the above params will resolved in favor of the supplied param
            :raises RequestException: if the connection failed
            :raises HumbleResponseException: if the response was invalid
            :raises HumbleCredentialException: if the username and password did not match
            :raises HumbleCaptchaException: if the captcha challenge failed
            :raises HumbleTwoFactorException: if the two-factor authentication challenge failed
            :raises HumbleAuthenticationException: if some other authentication error occurred
        """

        default_data = {
            "username": configuration.username,
            "password": configuration.password,
            "authy-token": configuration.authy_token
        }

        kwargs.setdefault("data", {}).update({k: v for k, v in default_data.items() if v is not None})

        response = self._request("POST", configuration.LOGIN_URL, *args, **kwargs)
        data = self.__parse_data(response)
        success = data.get("success", None)

        if success is True:
            self.session.cookies.save()
            return True

        authy_required = data.get("authy_required")
        errors, error_msg = self.__get_errors(data)
        request = response.request

        if errors:
            captcha = errors.get("captcha")
            username = errors.get("username")
            authy_token = errors.get("authy-token")

            if captcha:
                raise HumbleCaptchaException(
                    error_msg, request=request, response=response, authy_required=authy_required)

            if username:
                raise HumbleCredentialException(
                    error_msg, request=request, response=response, authy_required=authy_required)

            if authy_token:
                raise HumbleTwoFactorException(
                    error_msg, request=request, response=response, authy_required=authy_required)

        raise HumbleAuthenticationException(
            error_msg, request=request, response=response, uthy_required=authy_required)

    def get_gamekeys(self, *args, **kwargs):
        """
            Fetch all the gamekeys owned by an account.

            A gamekey is a string that uniquely identifies an order from the Humble store.

            :param list args: (optional) Extra positional args to pass to the request
            :param dict kwargs: (optional) Extra keyword args to pass to the request
            :return: A list of gamekeys
            :rtype: list
            :raises RequestException: if the connection failed
            :raises HumbleAuthenticationException: if not logged in
            :raises HumbleResponseException: if the response was invalid
        """

        response = self._request("GET", configuration.ORDER_LIST_URL, *args, **kwargs)

        """ get_gamekeys response always returns JSON """
        data = self.__parse_data(response)

        if isinstance(data, list):
            return [v["gamekey"] for v in data]

        # Let the helper function raise any common exceptions
        self.__authenticated_response_helper(response, data)

        # We didn't get a list, or an error message
        raise HumbleResponseException("Unexpected response body", request=response.request, response=response)

    def get_order(self, order_id, *args, **kwargs):
        """
            Download an order by its ID.

            :param order_id: The identifier ("gamekey") that uniquely identifies the order
            :param list args: (optional) Extra positional args to pass to the request
            :param dict kwargs: (optional) Extra keyword args to pass to the request
            :return: The :py:class:`Order` requested
            :rtype: Order
            :raises RequestException: if the connection failed
            :raises HumbleAuthenticationException: if not logged in
            :raises HumbleResponseException: if the response was invalid
        """
        url = configuration.ORDER_URL.format(order_id=order_id)
        response = self._request("GET", url, *args, **kwargs)

        """ order response might be 404 with no body if not found """

        if response.status_code == requests.codes.not_found:
            raise HumbleResponseException("Order not found", request=response.request, response=response)

        data = self.__parse_data(response)

        # The helper function should be sufficient to catch any other errors
        if self.__authenticated_response_helper(response, data):
            return Order(self, data)

    def _request(self, *args, **kwargs):
        """
            Set sane defaults that aren't session wide. Otherwise maintains the api of Session.request

            :param list args: (optional) Extra positional args to pass to the request
            :param dict kwargs: (optional) Extra keyword args to pass to the request
        """

        kwargs.setdefault("timeout", 30)
        return self.session.request(*args, **kwargs)

    @staticmethod
    def __get_errors(data):
        """
            Retrieves any errors defined within the JSON and returns them as a string.

            :param data: The JSON data to be searched for errors.
            :return:  A tuple containing the errors and error message.
        """
        errors = data.get("errors", None)
        error_msg = ", ".join(itertools.chain.from_iterable(v for k, v in errors.items())) \
            if errors else "Unspecified error"
        return errors, error_msg

    @staticmethod
    def __parse_data(response):
        """
            Try and parse the response data as JSON.  If parsing fails, throw a HumbleParseException.
        """
        try:
            return response.json()
        except ValueError as e:
            raise HumbleParseException("Invalid JSON: %s", str(e), request=response.request, response=response)

    def __authenticated_response_helper(self, response, data):
        # Successful API calls might not have a success property.
        # It"s not enough to check if it"s falsy, as None is acceptable
        success = data.get("success", None)
        if success:
            return True

        error_id = data.get("error_id", None)
        errors, error_msg = self.__get_errors(data)

        # API calls that require login and have a missing or invalid token.
        if error_id == "login_required":
            raise HumbleAuthenticationException(error_msg, request=response.request, response=response)

        # Something happened, we"re not sure what but we hope the error_msg is useful.
        if success is False or errors is not None or error_id is not None:
            raise HumbleResponseException(error_msg, request=response.request, response=response)

        # Response had no success or errors fields, it"s probably data
        return True
