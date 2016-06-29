"""
This includes common functions that are required when dealing with mails
"""
import socket
from exceptions import *
from constants import *
from email.header import decode_header
import email
import os
import hashlib


def get_mail_port(protocol, is_secure):
    """
    This returns the server port to use for POP retrieval of mails
    :param protocol: The protocol to be used to fetch emails - IMAP or POP3
    :type protocol: basestring
    :param is_secure: Determines if the mails should be fetced over SSL
    :type is_secure: bool
    :return: Returns the correct port for either POP3 or POP3 over SSL
    :rtype: int
    """
    port = 0
    if is_secure is True:
        if protocol == 'POP3':
            port = 995
        elif 'IMAP' == protocol:
            port = 993
        else:
            raise MailException("Invalid options passed to get_mail_port")
    elif is_secure is False:
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
    header_sections = [unicode(text, charset or default) for text, charset in headers]
    return u"".join(header_sections)


def process_raw_email(raw):
    """
    This fundtion takes an email in plain text form and preformats it with limited headers.
    :param raw: This represents the email in a bytearray to be processed
    :return: Returns a list with the [[date, Message-id, mail_message],...]
      :rtype: list
    """
    message = email.message_from_string(raw)
    print 'started processing'
    body = ''
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition')
            """
            body += "Content Disposition: %s\nContent Type: %s \n" % (repr(content_disposition) ,content_type)
            Microsoft sometimes sends the wrong content type. : sending csv as application/octect-stream

            """
            index_attachments_flag = INDEX_ATTACHMENT_DEFAULT
            extension = os.path.splitext(part.get_filename() or '')[1]
            if extension in SUPPORTED_FILE_EXTENSIONS:
                file_is_supported_attachment = True
            else:
                file_is_supported_attachment = False
            if content_type in SUPPORTED_CONTENT_TYPES or part.get_content_maintype() == 'text':
                content_type_supported = True
            else:
                content_type_supported = False

            if content_type_supported or file_is_supported_attachment:
                if content_disposition is not None and content_disposition != '':
                    if "attachment" in content_disposition and index_attachments_flag:
                        """Easier to change to a flag in inputs.conf"""
                        body += "\n#BEGIN_ATTACHMENT: %s\n" % part.get_filename()
                        body += "\n%s" % part.get_payload(decode=True)
                        body += "\n#END_ATTACHMENT: %s\n" % part.get_filename()
                    else:
                        body += "\n%s" % part.get_payload(decode=True)
                else:
                    body += "\n%s" % part.get_payload(decode=True)
            """
            else:
                body += "Found unsupported message part: %s, Filename: %s" % (content_type,part.get_filename())
            # what if we want to index images for steganalysis? - add an option for user to specify file extensions
            """
    else:
        body = message.get_payload(decode=True)
    mail_for_index = "Date: %s\n" \
                     "Message-ID: %s\n" \
                     "From: %s\n" \
                     "Subject: %s\n" \
                     "To: %s\n" \
                     "Body: %s\n" % (message['Date'], message['Message-ID'],
                                     message['From'], getheader(message['Subject']), message['To'], body)
    return [message['Date'], message['Message-ID'], mail_for_index]


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
