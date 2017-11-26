"""
This includes common functions that are required when dealing with mails
"""

from email.header import decode_header

try:
    from cStringIO import StringIO
    # cStringIO is faster
except ImportError:
    from StringIO import StringIO

MAIN_HEADERS = ('Date', 'Message-Id', 'Message-ID', 'From', 'To', 'Subject')
ZIP_EXTENSIONS = {'.zip', '.docx'}
EMAIL_PART = '$EMAIL$'
SUPPORTED_CONTENT_TYPES = {'application/xml', 'application/xhtml', 'application/x-sh', 'application/x-csh',
                           'application/javascript', 'application/bat', 'application/x-bat',
                           'application/x-msdos-program', 'application/textedit',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
TEXT_FILE_EXTENSIONS = {'.csv', '.txt', '.md', '.py', '.bat', '.sh', '.rb', '.js', '.asm'}
"""
It already indexes all text/* including:
    'text/plain', 'text/html', 'text/x-asm', 'text/x-c','text/x-python-script','text/x-python'
No need to add this to the supported types list
"""


def getheader(header_text, default="ascii"):
    """ This decodes sections of the email header which could be represented in utf8 or other iso languages"""
    headers = decode_header(header_text)
    header_sections = [unicode(text, charset or default, "ignore") for text, charset in headers]
    return u"".join(header_sections)


def recode_mail(part):
    cset = part.get_content_charset()
    if cset == "None":
        cset = "ascii"
    try:
        if not part.get_payload(decode=True):
            result = u''
        else:
            result = unicode(part.get_payload(decode=True), cset, "ignore").encode('utf8', 'xmlcharrefreplace').strip()
    except TypeError:
        result = part.get_payload(decode=True).encode('utf8', 'xmlcharrefreplace').strip()
    return result
