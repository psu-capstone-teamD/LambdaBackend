#!/usr/bin/python

# Authentication for a simple get request to Elemental Live.
# python auth_request.py --login <username> --api_key <api key> <url>
#
# link to Elemental's ruby version:
# https://github.com/guardian/content_delivery_system/blob/master/CDS/Ruby/lib/Elemental/auth_curl.rb

import argparse
import requests
import time
import hashlib

# parse login user and api-key
parser = argparse.ArgumentParser()
parser.add_argument('--login', nargs=1)
parser.add_argument('--api_key', nargs=1)
args = parser.parse_known_args()

headers = {"Accept":"", "X-Auth-User":"", "X-Auth-Expires":"", "X-Auth-Key":""}
api_key = args[0].api_key[0]
url = args[-1][0]    # url is last argument

# Set the response Type. Hardcoded as xml
headers["Accept"] = "application/xml"

# Set the user
headers["X-Auth-User"] = args[0].login[0]

# Set the time for session to expire. Should be ~30 seconds in the future
headers["X-Auth-Expires"] = str(int(time.time()) + 30)

# Set the auth key using this algorithm:
# md5(api_key + md5(url + X-Auth-User + api_key + X-Auth-Expires))

# Extract every part of the URL after /api and before headers
temp = url.partition("api")[2]
sub_url = temp.partition("?")[0]

string1 =(sub_url + headers["X-Auth-User"] + api_key + headers["X-Auth-Expires"]).encode('utf-8')
inner = hashlib.md5(string1).hexdigest()

string2 = (api_key + inner).encode('utf-8')
headers["X-Auth-Key"] = hashlib.md5(string2).hexdigest()

resp = requests.get(url, headers=headers)
print(resp.text)
