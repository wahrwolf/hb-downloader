from __future__ import division
from urlparse import urlparse
from HumbleHash import HumbleHash
from Events import Events
from humblebundle.exceptions import HumbleDownloadNeededException
import os
import requests
import configuration

__author__ = "Joel Pedraza"
__copyright__ = "Copyright 2014, Joel Pedraza"
__license__ = "MIT"


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

"""
    Order
    -]  Amount To Charge                                            amount_to_charge
    -]  Gamekey                                                     gamekey
    -]  Created                                                     created
    ->  Product                                                     product{}
        -]  Category                                                    category
        -]  Machine Name                                                machine_name
        -]  Post Purchase Text                                          post_purchase_text
        -]  Supports Canonical                                          supports_canonical
        -]  Human Name                                                  human_name
        -]  Partial Gift Enabled                                        partial_gift_enabled
    -> Subproducts                                                  subproducts{}
        -]  Machine Name                                                machine_name
        -]  URL                                                         url
        ->  Downloads                                                   downloads{}
            -]  Machine Name                                                machine_name
            -]  Platform                                                    platform
            ->  Options Dictionary                                          options_dict{}
            -]  Download Identifier                                         download_identifier
            -]  Android App Only                                            android_app_only
            -]  Download Version Number                                     download_version_number
            ->  Download Struct                                             download_struct{}
                -]  SHA1                                                        sha1
                -]  Name                                                        name
                ->  URL                                                         url{}
                    -]  Web URL                                                     web
                    -]  Bittorrent URL                                              bittorrent
                -]  Human Size                                                  human_size
                -]  File Size                                                   file_size
                -]  Small                                                       small
                -]  MD5                                                         md5
            -]  Custom Download Page Box HTML                               custom_download_page_box_html
            ->  Payee                                                       payee{}
                -]  Human Name                                                  human_name
                -]  Machine Name                                                machine_name
            -]  Human Name                                                  human_name
            -]  Library Family Name                                         library_family_name
            -]  Icon                                                        icon

    Need to implement handling of asmjs types.  Keys are dynamic for the manifest.
"""


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
