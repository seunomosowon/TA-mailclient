from utils import *

__version_info__ = (1, 3, 0)
__version__ = ".".join(map(str, __version_info__))
__all__ = ['ZIP_EXTENSIONS', 'TEXT_FILE_EXTENSIONS', 'SUPPORTED_CONTENT_TYPES',
           'email_mime', 'docx', 'zip']

# The following are available for use in additional parser definitions to be added into this module later:
# StringIO,
