""" Parse emails files """


import email
import os
import zip
# noinspection PyUnresolvedReferences
from email.Parser import Parser
from email.utils import mktime_tz, parsedate_tz
from .utils import *


def parse_email(email_as_string, include_headers):
    """
    This function parses an email and returns an array with different parts of the message.
    :param email_as_string: This represents the email in a bytearray to be processed
    :type email_as_string: basestring
    :param include_headers: This parameter specifies if all headers should be included.
    :type include_headers: bool
    :return: Returns a list with the [date, Message-id, mail_message]
      :rtype: list
    """
    message = email.message_from_string(email_as_string)
    mailheaders = Parser().parsestr(email_as_string, True)
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
