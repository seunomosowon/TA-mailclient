# DEFAULTS
IMAP_READONLY_FLAG = True
INDEX_ATTACHMENT_DEFAULT = True
DEFAULT_INCLUDE_HEADERS = True
DEFAULT_PROTOCOL_SECURITY = True
MAX_FETCH_COUNT = 25
REALM = 'mail'
PASSWORD_PLACEHOLDER = 'encrypted'
REGEX_EMAIL = r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'
REGEX_PASSWORD = r'^([\w!@#$%-]+)$'
REGEX_HOSTNAME = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|' \
                 r'[01]?[0-9][0-9]?)){3})$|^((([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])' \
                 r'\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]))$'
"""
It already indexes all text/* including:
    'text/plain', 'text/html', 'text/x-asm', 'text/x-c','text/x-python-script','text/x-python'
No need to add this to the supported types list
"""

DEFAULT_MAILBOX_CLEANUP = 'readonly'
MESSAGE_PREAMBLE = "VGhpcyBpcyBhIG1haWwgc2VwYXJhdG9yIGluIGJhc2U2NCBmb3Igb3VyIFNwbHVuayBpbmRleGluZwo=\n"


