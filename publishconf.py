# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *  # noqa: RUF100, E402, F403

# If your site is available via HTTPS, make sure SITEURL begins with https://
SITEURL = os.getenv("SITEURL")
RELATIVE_URLS = False

DELETE_OUTPUT_DIRECTORY = True
