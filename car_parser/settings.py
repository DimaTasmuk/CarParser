# -*- coding: utf-8 -*-

# Scrapy settings for car_parser project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SCRAPY_API_KEY = "b86dfa67fd4647dca2451627d5ff4a72"
SCRAPY_PROJECT_ID = "266968"

MONGO_URI = 'mongodb://Dima:Dima@ds153577.mlab.com:53577/autostore'
MONGO_DATABASE = 'autostore'

BOT_NAME = 'car_parser'

SPIDER_MODULES = ['car_parser.spiders']
NEWSPIDER_MODULE = 'car_parser.spiders'

# The default class that will be used for instantiating items in the Scrapy shell
#DEFAULT_ITEM_CLASS = 'car_parser.items.AutoDeCarItem'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

LOG_LEVEL = "INFO"
# LOG_LEVEL = "DEBUG"

COOKIES_ENABLED = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'car_parser.middlewares.CarParserSpiderMiddleware': 543,
#}
DOWNLOADER_MIDDLEWARES = {
    'car_parser.middleware.FilterMiddleware.FilterMiddleware': 300
}
# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES_BASE = {
#     'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 100,
#     'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 200,
#     'scrapy.downloadermiddlewares.retry.RetryMiddleware': 300,
#     'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 400,
#     'scrapy.downloadermiddlewares.stats.DownloaderStats': 500,
# }

# Change RetryMiddleware default setting
# RETRY_TIMES = 10
# RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 400]

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'car_parser.pipelines.DynamoPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
