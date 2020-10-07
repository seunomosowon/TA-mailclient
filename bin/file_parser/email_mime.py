""" Parse emails files """


import email
import re
import os
from . import zip
import hashlib
import quopri
# noinspection PyUnresolvedReferences
from base64 import b64decode
try:
    from email.parser import Parser
except ImportError:
    # Python 2
    from email.Parser import Parser
from email.utils import mktime_tz, parsedate_tz
from .utils import *

def parse_email(email_as_string, include_headers, maintain_rfc, attach_message_primary):
    """
    This function parses an email and returns an array with different parts of the message.
    :param email_as_string: This represents the email in a bytearray to be processed
    :type email_as_string: basestring
    :param include_headers: This parameter specifies if all headers should be included.
    :type include_headers: bool
    :param maintain_rfc: This parameter specifies if RFC format for email stays intact
    :type maintain_rfc: bool
    :param attach_message_primary: This parameter specifies if first attached email should
      be used as the message for indexing instead of the carrier email
    :type attach_message_primary: bool
    :return: Returns a list with the [date, Message-id, mail_message]
      :rtype: list
    """
    message = email.message_from_string(email_as_string)
    if attach_message_primary:
        message = change_primary_message(message)   
    if maintain_rfc:
        index_mail = maintain_rfc_parse(message)
    else:
        mailheaders = Parser().parsestr(message.as_string(), True)
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
                if extension in TEXT_FILE_EXTENSIONS or content_type in SUPPORTED_CONTENT_TYPES or \
                   part.get_content_maintype() == 'text' or extension in ZIP_EXTENSIONS:
                    if part.get_filename():
                        body.append("#BEGIN_ATTACHMENT: %s" % str(part.get_filename()))
                        if extension in ZIP_EXTENSIONS:
                            body.append("\n".join(zip.parse_zip(part, EMAIL_PART)))
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

def change_primary_message(message):
    """
    This function will look for an attached email and return it. This is inteded to use 
    the attached email as the email to be indexed instead of the carrier email.
    It checks if the message is already in message format or in a binary format and also
    only the first attached email will become the primary if there are more than one.
    :param message: This represents the email to be checked for attached email.
    :type message: email message object
    :return: Returns a email message object
      :rtype: email message object
    """
    for i in message.walk():
        if i.get_content_maintype()=='message':
            return i.get_payload()[0]
        elif i.get_content_subtype()=='octet-stream' and i.get_filename().lower().endswith('.eml'):
            if i['Content-Transfer-Encoding'].lower()=='base64': 
                return email.message_from_string(b64decode(i.get_payload()))
            else:
                return email.message_from_string(i.get_payload())

def maintain_rfc_parse(message):
    """
    This function parses an email and returns an array with different parts of the message
    but leaves the email still RFC compliant so that it works with Mail-Parser Plus app.
    Attachment headers are left in tact.
    :param message: This represents the email to be checked for attached email.
    :type message: email message object
    :return: Returns a email message formatted as a string
      :rtype: str
    """
    if not message.is_multipart():
        reformatted_message = quopri.decodestring(
                                message.as_string().encode('ascii', 'ignore')
                            ).decode("utf-8",'ignore')
        return reformatted_message
    boundary = message.get_boundary()
    new_payload = '--' + boundary
    for i in message.get_payload():
        content_type = i.get_content_type()
        extension = str(os.path.splitext(i.get_filename() or '')[1]).lower()
        if extension in TEXT_FILE_EXTENSIONS or content_type in SUPPORTED_CONTENT_TYPES or \
           i.get_content_maintype() == 'text':
            text_content = i.as_string().encode('ascii', 'ignore')
            text_content = quopri.decodestring(text_content).decode("utf-8",'ignore')
            new_payload += '\n' + text_content
        else:
            replace = re.sub(r'(?:\n\n)[\s\S]+',r'\n\n#UNSUPPORTED_ATTACHMENT:',i.as_string())
            filename = i.get_filename()
            charset = i.get_content_charset()
            try:
                md5 = hashlib.md5(i.get_payload(None,True)).hexdigest()
                sha256 = hashlib.sha256(i.get_payload(None,True)).hexdigest()
            except:
                md5 = ''
                sha256 = ''
            replace_string = """
file_name = %(filename)s
type = %(content_type)s
charset = %(charset)s
md5 = %(md5)s
sha256 = %(sha256)s
"""
            metadata = replace_string % dict(
                content_type=content_type, 
                filename=filename, 
                charset=charset,
                md5=md5,
                sha256=sha256,
            )
            new_payload += '\n' \
                + replace \
                + metadata
        new_payload += '\n--' + boundary
    new_payload += '--'
    message.set_payload(new_payload)
    return message.as_string()
