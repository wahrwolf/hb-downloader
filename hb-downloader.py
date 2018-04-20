#!/usr/bin/env python
import logger
from config_data import ConfigData
from configuration import Configuration
from event_handler import EventHandler
from humble_api.humble_api import HumbleApi
from humble_api.exceptions.humble_credential_exception import HumbleCredentialException
from humble_download import HumbleDownload
from progress_tracker import ProgressTracker

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


print("The Clown's Humble Bundle Downloader v%.2f" % ConfigData.VERSION)
print("")
print("This downloader includes MIT licensed code from Joel Pedraza.")
print("https://github.com/saik0/humblebundle-python")
print("")

# Load the configuration from the YAML file...
Configuration.load_configuration("hb-downloader-settings.yaml")
Configuration.parse_command_line()
Configuration.dump_configuration()
Configuration.push_configuration()

validation_status, message = Configuration.validate_configuration()
if not validation_status:
    logger.display_message(False, "Error", message)
    exit("Invalid configuration.  Please check your command line arguments and hb-downloader-settings.yaml.")

# Initialize the event handlers.
EventHandler.initialize()

hapi = HumbleApi(ConfigData.cookie_filename, ConfigData.auth_sess_cookie)

if not hapi.check_login():
    ConfigData.authy_token = input("Enter your Authy token: ")
    try:
        hapi.login(ConfigData.username, ConfigData.password, ConfigData.authy_token)
    except HumbleCredentialException as hce:
        logger.display_message(False, "Login", "Failed to login.  %s" % hce.message)
        exit("Login to humblebundle.com failed.  Please verify credentials and token.")

logger.display_message(False, "Processing", "Downloading order list.")
game_keys = hapi.get_gamekeys()
logger.display_message(False, "Processing", "%s orders found." % (len(game_keys)))

# Create initial list of Humble Downloads.  Filter out platforms which are turned off here.
ProgressTracker.reset()
ProgressTracker.item_count_total = len(game_keys)
download_size_total = 0
item_count_total = 0
key_downloads = dict()

for key in game_keys:
    ProgressTracker.item_count_current += 1
    logger.display_message(False, "Processing",
                           "Retrieving order details for order %s (%d/%d)." %
                           (key, ProgressTracker.item_count_current,
                            ProgressTracker.item_count_total))

    humble_downloads = HumbleDownload.needed_downloads_from_key(hapi, key)
    item_count_total += len(humble_downloads)
    download_size_total += sum(dl.humble_file_size for dl in humble_downloads)
    logger.display_message(False, "Processing",
                           "Added %d downloads for order %s"
                           % (len(humble_downloads), key))

    if len(humble_downloads) > 0:
        key_downloads[key] = humble_downloads

ProgressTracker.reset()
ProgressTracker.item_count_total = item_count_total
ProgressTracker.download_size_total = download_size_total

for key in key_downloads:
    HumbleDownload.update_download_list_url(hapi, key_downloads.get(key))
    for hd in key_downloads.get(key):
        ProgressTracker.assign_download(hd)
        ProgressTracker.display_summary()
        logger.display_message(False, "Download", hd.status_message)
        logger.display_message(False, "Download",
                               "Downloading %s." % hd.humble_file_size_human)
        hd.download_file()

        if hd.humble_file_size is not None:
            ProgressTracker.download_size_current += hd.humble_file_size
        ProgressTracker.item_count_current += 1

logger.display_message(False, "Processing", "Finished.")
exit()
