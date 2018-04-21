#!/usr/bin/env python
import logger
from config_data import ConfigData
from configuration import Configuration
from event_handler import EventHandler
from humble_api.humble_api import HumbleApi
from humble_api.exceptions.humble_credential_exception import HumbleCredentialException
from actions import Action

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

if ConfigData.action is "download":
    Action.batch_download(hapi, game_keys)
else:
    Action.list_downloads(hapi, game_keys)


exit()
