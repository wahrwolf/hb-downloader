#!/usr/bin/env python
import logging
import sys
from Events import Events
import humblebundle
import configuration
from humblebundle.exceptions import HumbleDownloadNeededException


def print_md5_start(filename):
    sys.stdout.write("[MD5] %s: " % filename)


def print_md5_end(filename):
    print ""


def print_download_start(filename):
    sys.stdout.write("[Download] %s: " % filename)


def print_download_end(filename):
    print ""


def print_progress(percentage):
    sys.stdout.write("{0:.0f}% ".format(percentage))


hapi = humblebundle.HumbleApi()

if hapi.check_login():
    pass
else:
    configuration.authy_token = raw_input("Enter your Authy token: ")
    hapi.login(configuration.username, configuration.password, configuration.authy_token)

print "The Clown's Humble Bundle Downloader v%.2f" % configuration.VERSION
print ""
print "This downloader includes MIT licensed code from Joel Pedraza."
print "https://github.com/saik0/humblebundle-python"
print ""

game_keys = hapi.get_gamekeys()
print "%s orders found." % (len(game_keys))

# Setup event handling for processing.
Events.on(configuration.EVENT_MD5_START, print_md5_start)
Events.on(configuration.EVENT_MD5_END, print_md5_end)
Events.on(configuration.EVENT_DOWNLOAD_START, print_download_start)
Events.on(configuration.EVENT_DOWNLOAD_END, print_download_end)
Events.on(configuration.EVENT_PROGRESS, print_progress)

for v in game_keys:
    order = hapi.get_order(v)

    for sp in order.subproducts or []:
        for d in sp.downloads or []:
            download_count = 0

            if not configuration.download_platforms.get(d.platform, False):
                print "Skipping %s/%s because it is not selected for download." % (d.machine_name, d.platform)
                continue

            for ds in d.download_structs:
                try:
                    if not len(ds.filename()) == 0:
                        download_count += 1
                        ds.is_already_downloaded(sp.product_name, d.platform)

                except HumbleDownloadNeededException as hdne:
                    print hdne.message
                    ds.download_file(sp.product_name, d.platform)

                if download_count == 0:
                    print "Skipping %s/%s because it has no downloads." % (d.machine_name, d.platform)
