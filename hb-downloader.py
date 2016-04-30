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


print "The Clown's Humble Bundle Downloader v%.2f" % ConfigData.VERSION
print ""
print "This downloader includes MIT licensed code from Joel Pedraza."
print "https://github.com/saik0/humblebundle-python"
print ""

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

hapi = HumbleApi(ConfigData.cookie_filename)

if not hapi.check_login():
    ConfigData.authy_token = raw_input("Enter your Authy token: ")
    try:
        hapi.login(ConfigData.username, ConfigData.password, ConfigData.authy_token)
    except HumbleCredentialException as hce:
        logger.display_message(False, "Login", "Failed to login.  %s" % hce.message)
        exit("Login to humblebundle.com failed.  Please verify credentials and token.")

logger.display_message(False, "Processing", "Downloading order list.")
game_keys = hapi.get_gamekeys()
logger.display_message(False, "Processing", "%s orders found." % (len(game_keys)))
humble_downloads = list()

# Create initial list of Humble Downloads.  Filter out platforms which are turned off here.
ProgressTracker.reset()
ProgressTracker.item_count_total = len(game_keys)

for cv in game_keys:
    ProgressTracker.item_count_current += 1
    logger.display_message(False, "Processing", "Retrieving order details for order %s (%d/%d)." %
                           (cv, ProgressTracker.item_count_current, ProgressTracker.item_count_total))
    co = hapi.get_order(cv)

    for csp in co.subproducts or []:
        for cd in csp.downloads or []:
            if not ConfigData.download_platforms.get(cd.platform, False):
                continue

            for cds in cd.download_structs:
                humble_downloads.append(HumbleDownload(cd, cds, co, csp, cv))

ProgressTracker.reset()
ProgressTracker.item_count_total = len(humble_downloads)
humble_downloads_required = list()

for hd in humble_downloads:
    ProgressTracker.item_count_current += 1
    ProgressTracker.assign_download(hd)
    ProgressTracker.display_summary()

    # logger.display_message(True, "Debug", "HD: %s" % hd.status())

    if hd.is_valid():
        if hd.check_status():
            logger.display_message(True, "Download", "%s (%s) already downloaded." %
                                   (hd.filename, hd.humble_file_size_human))
        else:
            logger.display_message(True, "Download", "%s" % hd.status_message)
            logger.display_message(True, "Download", "%s added to download queue." % hd.filename)
            humble_downloads_required.append(hd)

ProgressTracker.reset()
ProgressTracker.item_count_total = len(humble_downloads_required)

for hd in humble_downloads_required:
    ProgressTracker.download_size_total += hd.humble_file_size

for hd in humble_downloads_required:
    ProgressTracker.assign_download(hd)
    ProgressTracker.display_summary()
    logger.display_message(False, "Download", hd.status_message)
    logger.display_message(False, "Download", "Downloading %s." % hd.humble_file_size_human)
    hd.download_file()

    if hd.humble_file_size is not None:
        ProgressTracker.download_size_current += hd.humble_file_size

    ProgressTracker.item_count_current += 1

logger.display_message(False, "Processing", "Finished.")
exit()
