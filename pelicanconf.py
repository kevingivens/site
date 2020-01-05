#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Kevin Givens'
SITENAME = 'Lost in the Lyceum'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'America/New_York'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
FEED_ALL_RSS = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
#LINKS = (('Pelican', 'http://getpelican.com/'),
#         ('Python.org', 'http://python.org/'),
#         ('Jinja2', 'http://jinja.pocoo.org/'),
#         ('You can modify those links in your config file', '#'),)

# Template settings:
#DISPLAY_PAGES_ON_MENU
DISPLAY_CATEGORIES_ON_MENU = False
#MENUITEMS
#LINKS (Blogroll will be put in the sidebar instead of the head)

# Analytics & Comments
#GOOGLE_ANALYTICS (classic tracking code)
#GOOGLE_ANALYTICS_UNIVERSAL
#GOOGLE_ANALYTICS_UNIVERSAL_PROPERTY (Universal tracking code)
#DISQUS_SITENAME
#PIWIK_URL,
#PIWIK_SSL_URL
#PIWIK_SITE_ID

# Sidebar options

# Social widget
SOCIAL = (('twitter', 'https://twitter.com/kevinmgivens'),
          ('linkedin', 'https://www.linkedin.com/pub/kevin-m-givens/47/844/275'),
          ('github', 'https://github.com/kevingivens'),
          )

#DISPLAY_TAGS_ON_SIDEBAR = True and the tag_cloud plugin is enabled. Normally, tags are shown as a list.
#DISPLAY_TAGS_INLINE to True, to display the tags inline (ie. as tagcloud)
#TAGS_URL to the relative URL of the tags index page (typically tags.html)
DISPLAY_CATEGORIES_ON_SIDEBAR = True
#DISPLAY_RECENT_POSTS_ON_SIDEBAR is set to True
#RECENT_POST_COUNT to control the amount of recent posts. Defaults to 5
#DISPLAY_ARCHIVE_ON_SIDEBAR is set to True and
#MONTH_ARCHIVE_SAVE_AS is set up properly.
#DISPLAY_AUTHORS_ON_SIDEBAR is set to True

#Other sidebar related options include:

#HIDE_SIDEBAR to True.
#SIDEBAR_ON_LEFT to True.
#DISABLE_SIDEBAR_TITLE_ICONS to

DEFAULT_PAGINATION = 10

# Added for pelican bootstrap theme

PLUGIN_PATHS = ['../pelican-plugins', ]
PLUGINS = ['i18n_subsites', 'tipue_search', 'liquid_tags.notebook','render_math']
#PLUGINS = ['tipue_search','render_math']
JINJA_ENVIRONMENT = {
    'extensions': ['jinja2.ext.i18n'],
}

THEME = '../pelican-themes/pelican-bootstrap3'
THEME_STATIC_DIR = 'theme'
# static paths will be copied without parsing their contents
PATH = 'content'
STATIC_PATHS = ['blog','pages', 'images']
ARTICLE_PATHS = ['blog']
#STATIC_PATHS = ['images']
#ARTICLE_PATHS = ['']


BOOTSTRAP_THEME = 'flatly'
FAVICON = 'theme/images/icons/favicon.ico'

HIDE_SIDEBAR = False

# Article Info
#SHOW_ARTICLE_AUTHOR True to show the author of the article at the top of the article and in the index of articles.
#SHOW_ARTICLE_CATEGORY True to show the Category of each article.
#SHOW_DATE_MODIFIED True to show the article modified date next to the published date.

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# Pygments Style http://blog.yjl.im/2015/08/pygments-styles-gallery.html
PYGMENTS_STYLE = 'paraiso-dark'
#'tango'
#'colorful'
#'friendly'
#'manni'
#'monokai'

#NOTEBOOK_DIR = 'blog'

#SITELOGO = './theme/images/icons/favicon.ico'
#SITELOGO_SIZE

# Github
#GITHUB_USER = 'kevingivens'
#GITHUB_REPO_COUNT = False
#GITHUB_SKIP_FORK
#GITHUB_SHOW_USER_LINK = False

# Facebook Graph
USE_OPEN_GRAPH = True

# Discuss
#DISQUS_SITENAME = "blog-notmyidea"

# Twitter Cards
#TWITTER_CARDS
TWITTER_USERNAME = 'kevinmgivens'
TWITTER_WIDGET_ID = False

# Tipue Search
DIRECT_TEMPLATES = ('index', 'categories', 'authors', 'archives', 'search')
