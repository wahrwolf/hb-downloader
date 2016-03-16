#!/usr/bin/env python
import os
import sys
from configuration import Configuration
from humble_api.exceptions.humble_download_needed_exception import HumbleDownloadNeededException
from humble_api.humble_api import HumbleApi
from event_handler import EventHandler

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


print "The Clown's Humble Bundle Downloader v%.2f" % Configuration.VERSION
print ""
print "This downloader includes MIT licensed code from Joel Pedraza."
print "https://github.com/saik0/humblebundle-python"
print ""

# Load the configuration from the YAML file...
Configuration.load_configuration("hb-downloader-settings.yaml")
# configuration.parse_command_line(sys.argv)

validation_status, message = Configuration.validate_configuration()
if not validation_status:
    print message
    exit("Invalid configuration.  Please check your command line arguments and hb-downloader-settings.yaml.")

# Initialize the event handlers.
EventHandler.initialize()

hapi = HumbleApi(Configuration.cookie_filename)

if not hapi.check_login():
    Configuration.authy_token = raw_input("Enter your Authy token: ")
    hapi.login(Configuration.username, Configuration.password, Configuration.authy_token)

game_keys = hapi.get_gamekeys()
print "%s orders found." % (len(game_keys))

for v in game_keys:
    order = hapi.get_order(v)

    for sp in order.subproducts or []:
        for d in sp.downloads or []:
            download_count = 0

            if not Configuration.download_platforms.get(d.platform, False):
                print "Skipping %s/%s because it is not selected for download." % (d.machine_name, d.platform)
                continue

            for ds in d.download_structs:
                try:
                    if not len(ds.filename) == 0:
                        download_count += 1
                        if hapi.is_downloaded(Configuration.download_location, sp, d, ds):
                            print "%s already downloaded." % ds.filename

                except HumbleDownloadNeededException as hdne:
                    print hdne.message
                    hapi.download_file(Configuration.download_location, sp, d, ds)

                if download_count == 0:
                    print "Skipping %s/%s because it has no downloads." % (d.machine_name, d.platform)
