__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


class ConfigData(object):
    VERSION = 0.31
    username = ""
    password = ""
    authy_token = ""
    download_location = ""
    debug = True
    cookie_filename = "cookies.txt"
    write_md5 = True
    read_md5 = True
    force_md5 = False
    chunk_size = 8192000

    download_platforms = {
        'audio': True,
        'ebook': True,
        'windows': True,
        'mac': True,
        'linux': True,
        'android': True,
        'asmjs': False
    }
