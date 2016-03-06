#!/usr/bin/env python
VERSION = 0.1

# URLs.
LOGIN_URL = "https://www.humblebundle.com/login"
ORDER_LIST_URL = "https://www.humblebundle.com/api/v1/user/order"
ORDER_URL = "https://www.humblebundle.com/api/v1/order/{order_id}"

EVENT_MD5_START = "MD5_Start"
EVENT_MD5_END = "MD5_End"
EVENT_DOWNLOAD_START = "Download_Start"
EVENT_DOWNLOAD_END = "Download_End"
EVENT_PROGRESS = "Progress"

# Static variables related to configuration.
download_location = "/mnt/Storage/HumbleBundle/Games/"
cookie_filename = "cookies.txt"
username = ""
password = ""
authy_token = ""
chunk_size = 8192000
force_md5 = False
write_md5 = True
read_md5 = True
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

default_headers = {
    "Accept": "application/json",
    "Accept-Charset": "utf-8",
    "Keep-Alive": "true",
    "X-Requested-By": "hb_android_app",
    "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
}

default_params = {"ajax": "true"}
