import os
import yaml
import argparse
from humble_api.humble_hash import HumbleHash

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


class Configuration(object):
    VERSION = 0.3

    # Where files are stored upon download.
    # download_location = "/mnt/Storage/HumbleBundle/Games/"
    download_location = "\\\\megatron\\Mila\\Games\\Humble Bundle\\"

    username = ""
    password = ""
    authy_token = ""
    # Additional debugging information is stored in the objects and spewed in various places if this flag is set to true.
    debug = True
    # This is the name of the file where cookie information is stored after authentication.
    cookie_filename = "cookies.txt"

    download_platforms = {
        'audio': True,
        'ebook': True,
        'windows': True,
        'mac': True,
        'linux': True,
        'android': True,
        'asmjs': False
    }

    @staticmethod
    def validate_configuration():
        if not os.path.exists(Configuration.download_location):
            return False, "Download location doesn't exist"

        if not os.access(Configuration.download_location, os.W_OK | os.X_OK):
            return False, "Download location is not writable by the current user."

        if len(Configuration.username) == 0:
            return False, "The username for humblebundle.com has not been set."

        if len(Configuration.password) == 0:
            print False, "The password for humblebundle.com has not been set."

        return True, ""

    @staticmethod
    def load_configuration(config_file):
        with open(config_file, "r") as f:
            saved_config = yaml.safe_load(f)

        Configuration.download_platforms = saved_config.get("download-platforms", Configuration.download_platforms)
        HumbleHash.write_md5 = saved_config.get("write_md5", HumbleHash.write_md5)
        HumbleHash.read_md5 = saved_config.get("read_md5", HumbleHash.read_md5)
        HumbleHash.force_md5 = saved_config.get("force_md5", HumbleHash.force_md5)
        HumbleHash.chunk_size = saved_config.get("chunksize", HumbleHash.chunk_size)
        Configuration.debug = saved_config.get("debug", Configuration.debug)
        Configuration.download_location = saved_config.get("download-location", Configuration.download_location)
        Configuration.cookie_filename = saved_config.get("cookie-filename", Configuration.cookie_filename)
        Configuration.username = saved_config.get("username", Configuration.username)
        Configuration.password = saved_config.get("password", Configuration.password)

    @staticmethod
    def parse_command_line():
        parser = argparse.ArgumentParser()

        parser.add_argument("write_md5", nargs="?", default=Configuration.write_md5,
                            help="Write MD5 files for downloaded files.", type=bool)
        parser.add_argument("read_md5", nargs="?", default=Configuration.read_md5,
                            help="Read MD5 files for previously downloaded files.", type=bool)
        parser.add_argument("force_md5", nargs="?", default=Configuration.force_md5,
                            help="Force MD5 calculations.", type=bool)
        parser.add_argument("debug", nargs="?", default=Configuration.debug,
                            help="Toggles debug mode.", type=bool)
        parser.add_argument("download-location", nargs="?", default=Configuration.download_location,
                            help="Location to store downloaded files.", type=str)
        parser.add_argument("cookie-filename", nargs="?", default=Configuration.cookie_filename,
                            help="Location to store the cookie file.", type=str)
        parser.add_argument("username", nargs="?", default=Configuration.username,
                            help="Username for logging into humblebundle.com.", type=str)
        parser.add_argument("password", nargs="?", default=Configuration.password,
                            help="Password for logging into humblebundle.com.", type=str)
        parser.add_argument("chunksize", nargs="?", default=Configuration.chunk_size,
                            help="The size to use when calculating MD5s and downloading files.", type=long)

        parser.parse_args()

