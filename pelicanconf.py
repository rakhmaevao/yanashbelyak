import os

AUTHOR = "Александр Рахмаев"
SITENAME = "д. Янашбеляк"
SITEURL = os.getenv("SITEURL")
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

PLUGINS = [
    "pelican_embed_svg",
]

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True  # noqa: ERA001
