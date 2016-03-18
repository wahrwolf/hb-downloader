#!/usr/bin/env python
from configuration import Configuration
from humble_api.exceptions.humble_download_needed_exception import HumbleDownloadNeededException
from humble_api.exceptions.humble_credential_exception import HumbleCredentialException
from humble_api.humble_api import HumbleApi
from event_handler import EventHandler
from config_data import ConfigData
import logger

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
    Configuration.authy_token = raw_input("Enter your Authy token: ")
    try:
        hapi.login(ConfigData.username, ConfigData.password, ConfigData.authy_token)
    except HumbleCredentialException as hce:
        logger.display_message(False, "Login", "Failed to login.  %s" % hce.message)
        exit("Login to humblebundle.com failed.  Please verify credentials and token.")

game_keys = hapi.get_gamekeys()
logger.display_message(False, "Processing", "%s orders found." % (len(game_keys)))

for v in game_keys:
    order = hapi.get_order(v)
    logger.display_message(True, "Processing", "Processing product: %s" % order.product.human_name)

    num_sub_products = 0
    if order.subproducts is not None:
        logger.display_message(True, "Processing", "%s subproducts found." % (len(order.subproducts)))

    for sp in order.subproducts or []:
        logger.display_message(True, "Processing", "Current subproduct: %s" % sp.human_name)

        for d in sp.downloads or []:
            download_count = 0

            if not ConfigData.download_platforms.get(d.platform, False):
                logger.display_message(False, "Download",
                                       "Skipping %s/%s because platform is not selected for download." %
                                       (d.machine_name, d.platform))
                continue

            for ds in d.download_structs:
                try:
                    if not len(ds.filename) == 0:
                        download_count += 1
                        if hapi.is_downloaded(ConfigData.download_location, sp, d, ds):
                            logger.display_message(True, "Download", "%s (%s) already downloaded."
                                                   % (ds.filename, ds.human_size))

                except HumbleDownloadNeededException as hdne:
                    logger.display_message(False, "Download", "%s:  Downloading %s." % (hdne.message, ds.human_size))
                    hapi.download_file(ConfigData.download_location, sp, d, ds)

                if download_count == 0:
                    logger.display_message(True, "Download",
                                           "Skipping %s/%s because it has no downloads." %
                                           (d.machine_name, d.platform))
