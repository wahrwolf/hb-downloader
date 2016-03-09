from __future__ import division
import cookielib
import itertools
import os
from urlparse import urlparse
import requests
import configuration
from Events import Events
from HumbleHash import HumbleHash

"""
The Humble Bundle API client
"""

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"

__all__ = ["HumbleApi", "HumbleException", "HumbleResponseException", "HumbleAuthenticationException",
           "HumbleCredentialException", "HumbleCaptchaException", "HumbleTwoFactorException",
           "HumbleParseException", "HumbleDownloadNeededException", "BaseModel", "Order",
           "Product", "Subscription", "Payee", "Subproduct", "Download", "DownloadStruct"]


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


class HumbleException(Exception):
    """ An unspecified error occurred. """
    pass


class HumbleResponseException(requests.RequestException, HumbleException):
    """ A request completed but the response was somehow invalid or unexpected. """

    def __init__(self, *args, **kwargs):
        super(HumbleResponseException, self).__init__(*args, **kwargs)


class HumbleAuthenticationException(HumbleResponseException):
    """ An unspecified authentication failure occurred. """

    def __init__(self, *args, **kwargs):
        self.captcha_required = kwargs.pop("captcha_required", None)
        self.authy_required = kwargs.pop("authy_required", None)
        super(HumbleAuthenticationException, self).__init__(*args, **kwargs)


class HumbleCredentialException(HumbleAuthenticationException):
    """ Username and password don't match. """
    pass


class HumbleCaptchaException(HumbleAuthenticationException):
    """ The CAPTCHA response was invalid. """
    pass


class HumbleTwoFactorException(HumbleAuthenticationException):
    """ The one time password was invalid. """
    pass


class HumbleParseException(HumbleResponseException):
    """ An error occurred while parsing the response. """
    pass


class HumbleDownloadNeededException(HumbleResponseException):
    def __init__(self, message):
        self.message = message


class BaseModel(object):
    """ Represents the base object used by all of the Humble Bundle objects. """

    def __init__(self, client, data):
        """
            :param client: The client which is defining the object.
            :param data: The JSON data to define the object with.
        """
        self._client = client

        if configuration.debug:
            self._data = data

    def __unicode__(self):
        """
            Called by the str() built-in function and by the print statement to compute the
            "informal" string representation of an object.
        """
        return str({key: self.__dict__[key] for key in self.__dict__ if key != "_client"})

    def __str__(self):
        """
            Called by the str() built-in function and by the print statement to compute the
            "informal" string representation of an object encoded as ASCII.
        """
        return unicode(self).encode(u"utf-8")

    def __repr__(self):
        """
            Called by the repr() built-in function and by string conversions (reverse quotes) to
            compute the "official" string representation of an object. If at all possible, this
            should look like a valid Python expression that could be used to recreate an object
            with the same value (given an appropriate environment).
        """
        return repr(self.__dict__)

    def __iter__(self):
        """
           If a container object's __iter__() method is implemented as a generator, it will
           automatically return an iterator object (technically, a generator object) supplying
           the  __iter__() and next() methods.
        """
        return self.__dict__.__iter__()


class Order(BaseModel):
    """
        Represents a single order (Weekly Bundle, Monthly Bundle, etc.) which itself contains a list of
        subproducts which were a part of the order.
    """

    def __init__(self, client, data):
        super(Order, self).__init__(client, data)
        self.product = Product(client, data["product"])
        subscriptions_json = data.get("subscriptions", [])
        self.subscriptions = \
            [Subscription(client, sub) for sub in subscriptions_json] \
                if len(subscriptions_json) > 0 else None

        self.created = data.get("created", None)
        self.amount_to_charge = data.get("amount_to_charge", None)
        self.gamekey = data.get("gamekey", None)
        self.subproducts = ([Subproduct(client, prod) for prod in data.get("subproducts", [])]) or None

        # Former fields that I couldn't locate in my output:
        #   thankname, claimed, country, giftee, leaderboard, owner_username

    def __repr__(self):
        return "Order: <%s>" % self.product.machine_name


class Product(BaseModel):
    def __init__(self, client, data):
        super(Product, self).__init__(client, data)
        self.category = data.get("category", None)
        self.machine_name = data.get("machine_name", None)
        self.post_purchase_text = data.get("post_purchase_text", None)
        self.supports_canonical = data.get("supports_canonical", None)
        self.human_name = data.get("human_name", None)
        self.partial_gift_enabled = data.get("partial_gift_enabled", False)

    def __repr__(self):
        return "Product: <%s>" % self.machine_name


class Subscription(BaseModel):
    def __init__(self, client, data):
        super(Subscription, self).__init__(client, data)
        self.human_name = data.get("human_name", None)
        self.list_name = data.get("list_name", None)
        self.subscribed = data.get("subscribed", None)

    def __repr__(self):
        return "Subscription: <%s : %s>" % (self.list_name, self.subscribed)


class Payee(BaseModel):
    def __init__(self, client, data):
        super(Payee, self).__init__(client, data)
        self.human_name = data.get("human_name", None)
        self.machine_name = data.get("machine_name", None)

    def __repr__(self):
        return "Payee: <%s>" % self.machine_name


class Subproduct(BaseModel):
    def __init__(self, client, data):
        super(Subproduct, self).__init__(client, data)
        self.machine_name = data.get("machine_name", None)
        self.url = data.get("url", None)
        self.payee = Payee(client, data["payee"])
        self.downloads = [Download(client, download) for download in data["downloads"]]
        self.human_name = data.get("human_name", None)
        self.custom_download_page_box_html = data.get("custom_download_page_box_html", None)
        self.icon = data.get("icon", None)
        self.platform = data.get("platform", None)

    @property
    def product_name(self):
        if len(self.machine_name) == 0:
            return ""

        return_value = self.machine_name

        if return_value.endswith("withsoundtrack"):
            return_value = return_value.replace("withsoundtrack", "")

        underscore_index = return_value.find("_")
        if underscore_index != -1:
            return_value = return_value[0:underscore_index]

        return return_value

    def __repr__(self):
        return "Subproduct: <%s>" % self.machine_name


class Download(BaseModel):
    def __init__(self, client, data):
        super(Download, self).__init__(client, data)
        self.machine_name = data.get("machine_name", None)
        self.platform = data.get("platform", None)
        self.download_structs = [DownloadStruct(client, struct) for struct in data["download_struct"]]
        self.options_dict = data["options_dict"]
        self.download_identifier = data.get("download_identifier", None)
        self.download_version_number = data.get("download_version_number", None)
        self.android_app_only = data.get("android_app_only", False)

    def __repr__(self):
        return "Download: <%s>" % self.machine_name


class DownloadStruct(BaseModel):
    def __init__(self, client, data):
        super(DownloadStruct, self).__init__(client, data)
        self.sha1 = data.get("sha1", None)
        self.name = data.get("name", None)
        self.human_size = data.get("human_size", None)
        self.file_size = data.get("file_size", None)
        self.md5 = data.get("md5", None)

        self.download_web = None
        self.download_bittorrent = None

        url_dictionary = data.get("url", None)
        if url_dictionary is not None:
            self.download_web = url_dictionary.get("web", None)
            self.download_bittorrent = url_dictionary.get("bittorrent", None)

    def filename(self):
        work_value = ""

        if self.download_web is None and self.download_bittorrent is None:
            work_value = ""
        elif self.download_web is not None:
            work_value = self.download_web
        elif self.download_bittorrent is not None:
            work_value = self.download_bittorrent

        parsed_url = urlparse(work_value)
        filename = parsed_url[2]  # https://docs.python.org/2/library/urlparse.html

        if filename.startswith("/"):
            filename = filename[1:]
        filename = filename.replace("/", "_")

        return filename

    def is_already_downloaded(self, product, platform):
        full_filename = os.path.join(configuration.download_location, product, platform, self.filename())

        # If the file doesn't exist then we obviously don't have a match.
        # This is ignoring the whole possibility that the mount location may be invalid.
        if not os.path.exists(full_filename):
            raise HumbleDownloadNeededException("Target %s doesn't exist." % full_filename)

        # File size doesn't match?  No need to MD5 it.
        actual_file_size = os.path.getsize(full_filename)
        if actual_file_size != self.file_size:
            raise HumbleDownloadNeededException(
                "%s file sizes don't match (expected %d actual %d)." %
                (full_filename, self.file_size or 0, actual_file_size or 0))

        if not HumbleHash.check_hash(full_filename, self.md5):
            raise HumbleDownloadNeededException(
                "MD5 of %s doesn't match (expected %s)." % (full_filename, self.md5))

        return True

    def download_file(self, product, platform):
        full_directory = os.path.join(configuration.download_location, product, platform)
        if not os.path.exists(full_directory):
            os.makedirs(full_directory)

        full_filename = os.path.join(configuration.download_location, product, platform, self.filename())
        if os.path.exists(full_filename):
            os.remove(full_filename)
            HumbleHash.remove_md5file(full_filename)

        read_bytes = 0
        current_percentage = 0
        Events.trigger(configuration.EVENT_DOWNLOAD_START, full_filename)

        # TODO:  Handle when BT links exist but no web DL exists.
        r = requests.get(self.download_web, stream=True)
        with open(full_filename, "wb") as f:
            total_length = int(r.headers.get("content-length"))
            for chunk in r.iter_content(chunk_size=configuration.chunk_size):
                read_bytes += configuration.chunk_size
                read_bytes = min(total_length, read_bytes)

                current_percentage = self._check_percent(read_bytes, total_length, current_percentage)

                if chunk:
                    f.write(chunk)
                    f.flush()

        Events.trigger(configuration.EVENT_DOWNLOAD_END, full_filename)

    @staticmethod
    def _check_percent(current, total, current_percentage):
        percentage = current / total * 100
        percentage -= percentage % 10
        if current_percentage < percentage:
            current_percentage = percentage
            Events.trigger(configuration.EVENT_PROGRESS, current_percentage)

        return current_percentage
