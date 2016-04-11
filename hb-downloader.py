#!/usr/bin/env python
import logger
from config_data import ConfigData
from configuration import Configuration
from event_handler import EventHandler
from humble_api.humble_api import HumbleApi
from humble_api.exceptions.humble_credential_exception import HumbleCredentialException
from humble_api.exceptions.humble_download_needed_exception import HumbleDownloadNeededException
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

game_keys = hapi.get_gamekeys()
logger.display_message(False, "Processing", "%s orders found." % (len(game_keys)))

for cv in game_keys:
    ProgressTracker.order_count_total = len(game_keys)
    co = hapi.get_order(cv)

    if co.subproducts is not None:
        ProgressTracker.subproduct_count_total += len(co.subproducts)

        for csp in co.subproducts:
            if csp.downloads is not None:
                ProgressTracker.download_count_total += len(csp.downloads)

                for cd in csp.downloads:
                    if cd.download_structs is not None:
                        for cds in cd.download_structs:
                            if cds.file_size is not None:
                                ProgressTracker.download_size_total += cds.file_size

for v in game_keys:
    order = hapi.get_order(v)
    ProgressTracker.order_count_current += 1
    ProgressTracker.current_product = order.product.human_name

    for sp in order.subproducts or []:
        ProgressTracker.subproduct_count_current += 1
        ProgressTracker.current_subproduct = sp.human_name

        for d in sp.downloads or []:
            ProgressTracker.download_count_current += 1
            ProgressTracker.current_download = d.machine_name
            ProgressTracker.display_summary()
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
                    logger.display_message(False, "Download", "%s" % (hdne.message))
                    logger.display_message(False, "Download", "Downloading %s." % (ds.human_size))
                    hapi.download_file(ConfigData.download_location, sp, d, ds)

                if download_count == 0:
                    logger.display_message(True, "Download",
                                           "Skipping %s/%s because it has no downloads." %
                                           (d.machine_name, d.platform))

                if ds.file_size is not None:
                    ProgressTracker.download_size_current += ds.file_size

logger.display_message(False, "Processing", "Finished.")
exit()
