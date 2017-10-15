import argparse
import os
import yaml
import logger
from config_data import ConfigData
from humble_api.humble_hash import HumbleHash

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


class Configuration(object):
    @staticmethod
    def validate_configuration():
        """
            Does a basic validation of the configuration to ensure we're not missing
            anything critical.

            :return:  None
        """
        if not os.path.exists(ConfigData.download_location):
            return False, "Download location doesn't exist"

        if not os.access(ConfigData.download_location, os.W_OK | os.X_OK):
            return False, "Download location is not writable by the current user."

        if len(ConfigData.username) == 0:
            return False, "The username for humblebundle.com has not been set."

        if len(ConfigData.password) == 0:
            print(False, "The password for humblebundle.com has not been set.")

        return True, ""

    @staticmethod
    def load_configuration(config_file):
        """
            Loads configuration data from a yaml file.

            :param config_file:  The yaml file to load configuration data from.
            :return:  None
        """
        with open(config_file, "r") as f:
            saved_config = yaml.safe_load(f)

        ConfigData.download_platforms = saved_config.get("download-platforms", ConfigData.download_platforms)
        ConfigData.write_md5 = saved_config.get("write_md5", ConfigData.write_md5)
        ConfigData.read_md5 = saved_config.get("read_md5", ConfigData.read_md5)
        ConfigData.force_md5 = saved_config.get("force_md5", ConfigData.force_md5)
        ConfigData.chunk_size = saved_config.get("chunksize", ConfigData.chunk_size)
        ConfigData.debug = saved_config.get("debug", ConfigData.debug)
        ConfigData.download_location = saved_config.get("download-location", ConfigData.download_location)
        ConfigData.cookie_filename = saved_config.get("cookie-filename", ConfigData.cookie_filename)
        ConfigData.username = saved_config.get("username", ConfigData.username)
        ConfigData.password = saved_config.get("password", ConfigData.password)
        ConfigData.resume_downloads = saved_config.get("resume_downloads", ConfigData.resume_downloads)
        ConfigData.ignore_md5 = saved_config.get("ignore_md5", ConfigData.ignore_md5)

    @staticmethod
    def parse_command_line():
        """
            Parses configuration options from the command line arguments to the script.

            :return:  None
        """
        parser = argparse.ArgumentParser()

        parser.add_argument("-d", "--debug", nargs="?",
                            default=ConfigData.debug,
                            help="Toggles debug mode.", type=bool)
        parser.add_argument("-dl", "--download_location", nargs="?",
                            default=ConfigData.download_location,
                            help="Location to store downloaded files.", type=str)
        parser.add_argument("-cf", "--cookie_filename", nargs="?",
                            default=ConfigData.cookie_filename,
                            help="Location to store the cookie file.", type=str)
        parser.add_argument("-u", "--username", nargs="?",
                            default=ConfigData.username,
                            help="Username for logging into humblebundle.com.", type=str)
        parser.add_argument("-p", "--password", nargs="?",
                            default=ConfigData.password,
                            help="Password for logging into humblebundle.com.", type=str)
        parser.add_argument("-cs", "--chunksize", nargs="?",
                            default=ConfigData.chunk_size,
                            help="The size to use when calculating MD5s and downloading files.", type=int)

        args = parser.parse_args()

        ConfigData.debug = args.debug

        ConfigData.username = args.username
        ConfigData.password = args.password
        ConfigData.cookie_filename = args.cookie_filename
        ConfigData.download_location = args.download_location
        ConfigData.chunk_size = args.chunksize

    @staticmethod
    def dump_configuration():
        """
            Dumps the current configuration to the log.  Username and password are not dumped to
            allow logs or output to be posted without fear of personal information.

            :return: None
        """
        # Shortcut the process if debugging is not turned on.
        if not ConfigData.debug:
            return

        logger.display_message(True, "Config", "write_md5=%s" % ConfigData.write_md5)
        logger.display_message(True, "Config", "read_md5=%s" % ConfigData.read_md5)
        logger.display_message(True, "Config", "force_md5=%s" % ConfigData.force_md5)
        logger.display_message(True, "Config", "ignore_md5=%s" % ConfigData.ignore_md5)
        logger.display_message(True, "Config", "debug=%s" % ConfigData.debug)
        logger.display_message(True, "Config", "download_location=%s" % ConfigData.download_location)
        logger.display_message(True, "Config", "cookie_filename=%s" % ConfigData.cookie_filename)
        logger.display_message(True, "Config", "chunksize=%s" % ConfigData.chunk_size)
        logger.display_message(True, "Config", "resume_downloads=%s" % ConfigData.resume_downloads)

        for platform in list(ConfigData.download_platforms.keys()):
            logger.display_message(True, "Config", "Platform %s=%s" %
                                   (platform, ConfigData.download_platforms[platform]))

    @staticmethod
    def push_configuration():
        """
            Pushes configuration variables down to lower libraries which require them.

            :return: None
        """
        HumbleHash.write_md5 = ConfigData.write_md5
        HumbleHash.read_md5 = ConfigData.read_md5
        HumbleHash.force_md5 = ConfigData.force_md5
        HumbleHash.chunk_size = ConfigData.chunk_size
