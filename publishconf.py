# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *

# If your site is available via HTTPS, make sure SITEURL begins with https://
SITEURL = "https://rahmaevao.github.io/yanashbelyak"
RELATIVE_URLS = False

DELETE_OUTPUT_DIRECTORY = True

AUTHOR = "Александр Рахмаев"
SITENAME = "д. Янашбеляк"
# SITEURL = "https://rahmaevao.github.io/yanashbelyak"
# SITEURL = "http://127.0.0.1:8000"
OUTPUT_PATH = "docs"
PATH = "content"

TIMEZONE = "Europe/Moscow"

DEFAULT_LANG = "ru"

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True
