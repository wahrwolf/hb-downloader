from __future__ import division
import cookielib
import itertools
import os
from model.order import Order
import requests
from events import Events
from humble_hash import HumbleHash
from model.subproduct import Subproduct
from model.download import Download
from model.download_struct import DownloadStruct
from exceptions.humble_download_needed_exception import HumbleDownloadNeededException
from exceptions.humble_response_exception import HumbleResponseException
from exceptions.humble_authentication_exception import HumbleAuthenticationException
from exceptions.humble_captcha_exception import HumbleCaptchaException
from exceptions.humble_credential_exception import HumbleCredentialException
from exceptions.humble_two_factor_exception import HumbleTwoFactorException
from exceptions.humble_parse_exception import HumbleParseException

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"

__all__ = ["HumbleApi"]


class HumbleApi(object):
    """
        This class represents common actions for the Humble API.

        The Humble Bundle API is not stateless, it stores an authentication token as a cookie named _simpleauth_sess

        The Requests.Session handles storing the auth token. To load some persisted cookies simply set session.cookies
        after initialization.
    """

    # URLs.
    LOGIN_URL = "https://www.humblebundle.com/login"
    ORDER_LIST_URL = "https://www.humblebundle.com/api/v1/user/order"
    ORDER_URL = "https://www.humblebundle.com/api/v1/order/{order_id}"

    # default_headers specifies the default HTTP headers added to each request sent to the humblebundle.com servers.
    default_headers = {
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
        "Keep-Alive": "true",
        "X-Requested-By": "hb_android_app",
        "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    }

    # default_params specifies the default querystring parameters added to each request sent to humblebundle.com.
    default_params = {"ajax": "true"}

    def __init__(self, cookie_location="cookie.txt"):
        """
            Base constructor.  Responsible for setting up the requests object and cookie jar.
            All configuration values should be set prior to constructing an object of this
            type; changes to configuration will not take effect on variables which already
            exist.
        """
        self.session = requests.Session()
        try:
            self.session.cookies = cookielib.LWPCookieJar(cookie_location)
        except IOError:
            # Cookie file doesn't exist.
            pass

        self.session.cookies.load()
        self.session.headers.update(self.default_headers)
        self.session.params.update(self.default_params)

    def check_login(self):
        """
            Checks to see if we have a valid session cookie by attempting to retrieve the orders page.
            If we get a HumbleAuthenticationException then we need to log in to the system again.
            Otherwise we're good to go.

            We can't just check for the cookie existence.  The session ID might've been
            invalidated server side.

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

    def login(self, username, password, authy_token, *args, **kwargs):
        """
            Login to the Humble Bundle API.

            The response sets the _simpleauth_sess cookie which is stored in the session
            automatically.

            :param str username:  The username to use when logging into humblebundle.com.
            :param str password:  The password to use when logging into humblebundle.com.
            :param str authy_token:  The Authy token to use when logging into humblebundle.com.
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
            "username": username,
            "password": password,
            "authy-token": authy_token
        }

        kwargs.setdefault("data", {}).update({k: v for k, v in default_data.items() if v is not None})

        response = self._request("POST", self.LOGIN_URL, *args, **kwargs)
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
        response = self._request("GET", HumbleApi.ORDER_LIST_URL, *args, **kwargs)

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
        url = HumbleApi.ORDER_URL.format(order_id=order_id)

        response = self._request("GET", url, *args, **kwargs)

        """ order response might be 404 with no body if not found """

        if response.status_code == requests.codes.not_found:
            raise HumbleResponseException("Order not found", request=response.request, response=response)

        data = self.__parse_data(response)

        # The helper function should be sufficient to catch any other errors
        if self.__authenticated_response_helper(response, data):
            return Order(data)

    def _request(self, *args, **kwargs):
        """
            Set sane defaults that aren't session wide. Otherwise maintains the API of Session.request.

            :param list args: (optional) Extra positional args to pass to the request.
            :param dict kwargs: (optional) Extra keyword args to pass to the request.
        """
        kwargs.setdefault("timeout", 30)
        return self.session.request(*args, **kwargs)

    def download_file(self, download_location, sp, d, ds, chunk_size=8192000):
        """
            Downloads a file from the location specified in the provided DownloadStruct.

            :param download_location:  The location to place downloaded files.
            :param sp:  The Subproduct associated with the DownloadStruct.
            :param d:  The Download associated with the DownloadStruct.
            :param ds:  The DownloadStruct to use for identifying the files to download.
            :param chunk_size:  The chunk size to use when downloading a file.
        """
        assert isinstance(download_location, str)
        assert isinstance(sp, Subproduct)
        assert isinstance(d, Download)
        assert isinstance(ds, DownloadStruct)

        full_directory = os.path.join(download_location, sp.product_name, d.platform)
        if not os.path.exists(full_directory):
            os.makedirs(full_directory)

        full_filename = os.path.join(download_location, sp.product_name, d.platform, ds.filename)
        if os.path.exists(full_filename):
            os.remove(full_filename)
            HumbleHash.remove_md5file(full_filename)

        read_bytes = 0
        current_percentage = 0
        Events.trigger(Events.EVENT_DOWNLOAD_START, full_filename)

        # TODO:  Handle when BT links exist but no web DL exists.
        r = requests.get(ds.download_web, stream=True)
        with open(full_filename, "wb") as f:
            total_length = int(r.headers.get("content-length"))
            for chunk in r.iter_content(chunk_size=chunk_size):
                read_bytes += chunk_size
                read_bytes = min(total_length, read_bytes)

                current_percentage = Events.check_percent(read_bytes, total_length, current_percentage)

                if chunk:
                    f.write(chunk)
                    f.flush()

        Events.trigger(Events.EVENT_DOWNLOAD_END, full_filename)

    def is_downloaded(self, download_location, sp, d, ds):
        """
            This method determines whether or not the given file has already been successfully downloaded.

            :param download_location:  The location to place downloaded files.
            :param sp:  The Subproduct associated with the DownloadStruct.
            :param d:  The Download associated with the DownloadStruct.
            :param ds:  The DownloadStruct to use for identifying the files to download.
            :return:  True if the existing file matches size and checksum verification.
            :rtype:  bool
        """
        assert isinstance(download_location, str)
        assert isinstance(sp, Subproduct)
        assert isinstance(d, Download)
        assert isinstance(ds, DownloadStruct)

        full_filename = os.path.join(download_location, sp.product_name, d.platform, ds.filename)

        # If the file doesn't exist then we obviously don't have a match.
        # This is ignoring the whole possibility that the mount location may be invalid.
        if not os.path.exists(full_filename):
            raise HumbleDownloadNeededException("Target %s doesn't exist." % full_filename)

        # File size doesn't match?  No need to MD5 it.
        actual_file_size = os.path.getsize(full_filename)
        if actual_file_size != ds.file_size:
            raise HumbleDownloadNeededException(
                "%s file sizes don't match (expected %d actual %d)." %
                (full_filename, ds.file_size or 0, actual_file_size or 0))

        if not HumbleHash.verify_checksum(full_filename, ds.md5):
            raise HumbleDownloadNeededException(
                "MD5 of %s doesn't match (expected %s)." % (full_filename, ds.md5))

        return True

    def __authenticated_response_helper(self, response, data):
        """
            Checks a response for the common authentication errors.  Sometimes a successful API call won't have a
             success property.  We do a check for this property and return true if found, otherwise we parse for
             errors.

            :param response:  The response received from humblebundle.com. A pass through variable used to initialize
             the exceptions.
            :param data:  The interpreted JSON data from the response.
            :return:  True if the API call was successful.  Otherwise an exception is thrown.
            :raises HumbleAuthenticationException: If not logged in.
            :raises HumbleResponseException: If the response was invalid.
        """
        success = data.get("success", None)
        if success:
            return True

        error_id = data.get("error_id", None)
        errors, error_msg = self.__get_errors(data)

        # API calls that require login and have a missing or invalid token.
        if error_id == "login_required":
            raise HumbleAuthenticationException(error_msg, request=response.request, response=response)

        # Something happened, we're not sure what but we hope the error_msg is useful.
        if success is False or errors is not None or error_id is not None:
            raise HumbleResponseException(error_msg, request=response.request, response=response)

        # Response had no success or errors fields, it's probably data
        return True

    def __parse_data(self, response):
        """
            Try and parse the response data as JSON.  If parsing fails, throw a HumbleParseException.

            :param response:  The response received from humblebundle.com.
             A pass through variable used to initialize the exceptions.
            :return:  The response as a JSON object.
            :raises HumbleParseException:  When the response cannot be parsed as a JSON object.
        """
        try:
            return response.json()
        except ValueError as e:
            raise HumbleParseException("Invalid JSON: %s", str(e), request=response.request, response=response)

    def __get_errors(self, data):
        """
            Retrieves any errors defined within the JSON and returns them as a string.

            :param data: The JSON data to be searched for errors.
            :return:  A tuple containing the errors and error message.
        """
        errors = data.get("errors", None)
        error_msg = ", ".join(itertools.chain.from_iterable(v for k, v in errors.items())) \
            if errors else "Unspecified error"
        return errors, error_msg
