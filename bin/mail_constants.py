# DEFAULTS
from __future__ import unicode_literals

IMAP_READONLY_FLAG = True
INDEX_ATTACHMENT_DEFAULT = True
DEFAULT_INCLUDE_HEADERS = True
DEFAULT_MAINTAIN_RFC = False
DEFAULT_ATTACH_MESSAGE_PRIMARY = False
DEFAULT_PROTOCOL_SECURITY = True
DEFAULT_MAILBOX_CLEANUP = 'readonly'
MAX_FETCH_COUNT = 25
REALM = 'mail'
PASSWORD_PLACEHOLDER = 'encrypted'
REGEX_EMAIL = r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'
REGEX_PASSWORD = r'^([\w!@#$%-]+)$'
REGEX_HOSTNAME = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|' \
                 r'[01]?[0-9][0-9]?)){3})$|^((([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])' \
                 r'\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]))$'
MESSAGE_PREAMBLE = "VGhpcyBpcyBhIG1haWwgc2VwYXJhdG9yIGluIGJhc2U2NCBmb3Igb3VyIFNwbHVuayBpbmRleGluZwo=\n"
