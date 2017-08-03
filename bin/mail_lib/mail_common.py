"""
This includes common functions that are required when dealing with mails
"""
import email
import hashlib
import os
import socket
import zipfile
from email.header import decode_header
# noinspection PyUnresolvedReferences
from email.Parser import Parser
from email.utils import mktime_tz, parsedate_tz
from xml.dom.minidom import parse as parsexml
import sys
from .constants import *
from .exceptions import *


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class Capturing(list):
    """ Thanks to Kindall and other examples on stackoverflow """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def get_mail_port(protocol, is_secure):
    """
    This returns the server port to use for POP retrieval of mails
    :param protocol: The protocol to be used to fetch emails - IMAP or POP3
    :type protocol: basestring
    :param is_secure: Determines if the mails should be fetched over SSL
    :type is_secure: bool
    :return: Returns the correct port for either POP3 or POP3 over SSL
    :rtype: int
    """
    if is_secure:
        if protocol == 'POP3':
            port = 995
        elif 'IMAP' == protocol:
            port = 993
        else:
            raise MailException("Invalid options passed to get_mail_port")
    else:
        if protocol == 'POP3':
            port = 110
        elif protocol == 'IMAP':
            port = 143
        else:
            raise MailException("Invalid options passed to get_mail_port")
    return port


def mail_connectivity_test(server, protocol, is_secure):
    """
    This validates connectivity to given hostname and port
    :param server: This is the remote hostname or IP to be used for the test.
    :type server: basestring
    :param protocol: The protocol to be used to fetch emails - IMAP or POP3
    :type protocol: basestring
    :param is_secure: true/false
    :type is_secure: bool
    :return: Raises an exception back to the modinput validation if connectivity test fails
    """
    try:
        captive_dns_addr = socket.gethostbyname(server)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((captive_dns_addr, get_mail_port(protocol=protocol, is_secure=is_secure)))
        s.close()
    except socket.error, e:
        raise socket.error("Socket error : %s" % e)


def getheader(header_text, default="ascii"):
    """ This decodes sections of the email header which could be represented in utf8 or other iso languages"""
    headers = decode_header(header_text)
    header_sections = [unicode(text, charset or default, "ignore") for text, charset in headers]
    return u"".join(header_sections)


def read_docx(decoded_payload):
    """
    This reads a docx file form a string and outputs just the text from the document
    along with the document's internal structure
    :param decoded_payload: This is a the payload from an email that contains a docx file
    :return: This returns the texts from the word document.
    :rtype: basestring
    """
    # decoded_payload = open('a.docx', 'r').read()
    fp = StringIO(decoded_payload)
    zfp = zipfile.ZipFile(fp)
    if zfp:
        y = parsexml(zfp.open('[Content_Types].xml', 'rU')).documentElement.toprettyxml()
        """
        I can check for Macros here
        if zfp.getinfo('word/vbaData.xml'):
        openXML standard supports any name for xml file. Need to check all files.
        Add the contents pages to the top of word file for visual inspection of macros
        """
        if zfp.getinfo('word/document.xml'):
            doc_xml = parsexml(zfp.open('word/document.xml', 'rU'))
            y += u''.join([node.firstChild.nodeValue for node in doc_xml.getElementsByTagName('w:t')])
        else:
            y = u'Not yet supported docx file'
    else:
        y = u'Email attachment did not match Word / OpenXML document format'
    return y


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


def process_raw_email(raw, include_headers):
    """
    This function takes an email in plain text form and preformats it with limited headers.
    :param raw: This represents the email in a bytearray to be processed
    :type raw: basestring
    :param include_headers: This parameter specifies if all headers should be included.
    :type include_headers: bool
    :return: Returns a list with the [[date, Message-id, mail_message],...]
      :rtype: list
    """
    message = email.message_from_string(raw)
    mailheaders = Parser().parsestr(raw, True)
    headers = ["%s: %s" % (k, getheader(v)) for k, v in mailheaders.items() if k in MAIN_HEADERS]
    if include_headers:
        other_headers = ["%s: %s" % (k, getheader(v)) for k, v in mailheaders.items() if k not in MAIN_HEADERS]
        headers.extend(other_headers)
    body = []
    if message.is_multipart():
        part_number = 1
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition')
            if content_type in ['multipart/alternative', 'multipart/mixed']:
                # The multipart/alternative part is usually empty.
                body.append("Multipart envelope header: %s" % str(part.get_payload(decode=True)))
                continue
            body.append("#START_OF_MULTIPART_%d" % part_number)
            extension = str(os.path.splitext(part.get_filename() or '')[1]).lower()
            if extension in SUPPORTED_FILE_EXTENSIONS or content_type in SUPPORTED_CONTENT_TYPES or \
               part.get_content_maintype() == 'text':
                if part.get_filename():
                    body.append("#BEGIN_ATTACHMENT: %s" % str(part.get_filename()))
                    if extension == '.docx':
                        body.append(read_docx(part.get_payload(decode=True)))
                    else:
                        body.append(recode_mail(part))
                    body.append("#END_ATTACHMENT: %s" % str(part.get_filename()))
                else:
                    body.append(recode_mail(part))
            else:
                body.append("#UNSUPPORTED_ATTACHMENT: file_name = %s - type = %s ; disposition=%s" % (
                    part.get_filename(), content_type, content_disposition))
            body.append("#END_OF_MULTIPART_%d" % part_number)
            part_number += 1
    else:
        body.append(recode_mail(message))
    """mail_for_index = [MESSAGE_PREAMBLE]"""
    mail_for_index = []
    mail_for_index.extend(headers + body)
    index_mail = "\n".join(mail_for_index)
    message_time = float(mktime_tz(parsedate_tz(message['Date'])))
    return [message_time, message['Message-ID'], index_mail]


def save_checkpoint(checkpoint_dir, msg):
    """
    This creates a checkpoint file in the checkpoint directory for the message.
    :param checkpoint_dir: This contains the path where checkpoint files will be saved
    :type checkpoint_dir: basestring
    :param msg: Contains a message that needs to indexed and
     :type msg: basestring
    """
    filename = os.path.join(checkpoint_dir, hashlib.sha256(str(msg)).hexdigest())
    f = open(filename, 'w')
    f.close()


def locate_checkpoint(checkpoint_dir, msg):
    """
    This checks if a message has already been indexed by using a digest of the first 300 characters,
    which includes a date, message id, source and destination email addresses.
    :param checkpoint_dir: This contains the path where checkpoint files will be saved
    :type checkpoint_dir: basestring
    :param msg: Contains a message that needs to indexed and
     :type msg: basestring
    :return: Returns true if the message has been indexed previously, and false if not.
     :rtype: bool
    """
    filename = os.path.join(checkpoint_dir, hashlib.sha256(str(msg)).hexdigest())
    try:
        open(filename, 'r').close()
    except (OSError, IOError):
        return False
    return True


def bool_variable(x):
    if x == "enabled":
        x = True
    elif x == "disabled":
        x = False
    elif x is "1" or x is "0":
        x = bool(int(x))
    else:
        x = bool(int(1))
    return x
