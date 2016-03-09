#!/usr/bin/env python
import os
import sys

__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


VERSION = 0.2

# URLs.
LOGIN_URL = "https://www.humblebundle.com/login"
ORDER_LIST_URL = "https://www.humblebundle.com/api/v1/user/order"
ORDER_URL = "https://www.humblebundle.com/api/v1/order/{order_id}"

# These are used to define the name of the corresponding events.  Defined as
# constants to avoid typos and the resulting frustration.
EVENT_MD5_START = "MD5_Start"
EVENT_MD5_END = "MD5_End"
EVENT_DOWNLOAD_START = "Download_Start"
EVENT_DOWNLOAD_END = "Download_End"
# This event is fired every time the progress of an MD5 or download increases
# by 10% or more from the previous status.
EVENT_PROGRESS = "Progress"

# Static variables related to configuration.
# Where files are stored upon download.  If using a Windows box ensure you
# use double slashes for each location, aka "C:\\Users\\bmschke\\Downloads".
# Trailing slash is irrelevant.
download_location = "/mnt/Storage/HumbleBundle/Games/"
# This is the name of the file where cookie information is stored after
# authentication.  You can include a full path if you want this stored in
# a specific location.
cookie_filename = "cookies.txt"
username = ""
password = ""
authy_token = ""
# The chunk size is used when working with MD5 calculation and downloading from
# the web.  Larger chunk sizes work faster - but you receive fewer progress
# notifications.  This is also a large determining factor on the maximum amount
# of memory the script will use.
chunk_size = 8192000
# FORCE_MD5 forces an MD5 calculation for every existing file every execution.
force_md5 = False
# WRITE_MD5 indicates whether MD5 files should be written for files after calculation.
# The format is filename.ext.md5.  The format written is (hopefully :)) equivalent
# to md5sum.  (https://en.wikipedia.org/wiki/Md5sum)  The script doesn't yet
# combine MD5 hashes into one file however - it is one .md5 file per download.
write_md5 = True
# READ_MD5 indicates whether .md5 files should be read if they're available.  If this
# option is enabled the value in the .md5 file will be used in place of a live MD5
# calculation.
read_md5 = True
# Additional debugging information is stored in the objects and spewed in various places
# if this flag is set to true.
debug = True

download_platforms = {
    'audio': True,
    'ebook': True,
    'windows': True,
    'mac': True,
    'linux': True,
    'android': True,
    'asmjs': False
}

# DEFAULT_HEADERS specifies the default HTTP headers added to each request sent to the
# humblebundle.com servers.
default_headers = {
    "Accept": "application/json",
    "Accept-Charset": "utf-8",
    "Keep-Alive": "true",
    "X-Requested-By": "hb_android_app",
    "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
}

default_params = {"ajax": "true"}


def convert_to_bool(user_input, default_value=False):
    if len(user_input) == 0:
        return default_value

    user_input = user_input[0].upper()

    if user_input == 'Y' or user_input == 'T':
        return True

    if user_input == 'N' or user_input == 'F':
        return False

    return default_value

input_download_location = raw_input("Enter the location to download files: ")
if not os.path.exists(input_download_location):
    print "Download location doesn't exist.  It will be created at runtime as needed if not created."
    create_download_location = raw_input("Do you want me to create it now? [Y/n]")
    if convert_to_bool(create_download_location, True):
        try:
            os.makedirs(create_download_location)
        except OSError as ose:
            print "There was an error while creating the specified download location."
            print ose.message
            sys.exit(os.EX_OSFILE)


print "\nThe following information will be stored in plain text in your configuration file."
print "It is required for the script to execute; this notice is for full disclosure only."

print "Your Humble Bundle username is generally an email address."
input_username = raw_input("Enter your username: ")
input_password = raw_input("Enter your password: ")

print "\nYour Authy token will be prompted for upon the first execution of the script."
print "After the first execution the _simpleauth_sess cookie should be sufficient for authorization."

