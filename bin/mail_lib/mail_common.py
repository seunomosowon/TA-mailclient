"""
This includes common functions that are required when dealing with mails
"""
import socket
from exceptions import *
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
    port=0
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


def process_raw_email(raw):
    """
    This fundtion takes an email in plain text form and preformats it with limited headers.
    :param raw: This represents the email in a bytearray to be processed
    :return: Returns a list with the [[date,mail_message],]
      :rtype: list
    """
    message = email.message_from_string(raw)
    body = ''
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if 'text/plain' == content_type or 'text/html' == content_type:
                body += '\n' + part.get_payload()
    else:
        body = message.get_payload()
    mail_for_index = "Date: %s\n" \
                     "Message-ID: %s\n" \
                     "From: %s\n" \
                     "Subject: %s\n" \
                     "To: %s\n" \
                     "Body: %s\n" % (message['Date'], message['Message-ID'],
                                     message['From'], message['Subject'], message['To'], body)
    return [message['Date'], mail_for_index]


def save_checkpoint(inputs, msg):
    """
    This creates a checkpoint file in the checkpoint directory for the message.
    :param inputs: contains the input definition which includes the path to its checkpoint directory
     :type inputs: splunklib.modularinput.Inputdefinition
    :param msg: Contains a message that needs to indexed and
     :type msg: basestring
    """
    h = hashlib.new('sha256')
    h.update(msg[0:300])
    checkpoint_dir = inputs.metadata['checkpoint_dir']
    filename = os.path.join(checkpoint_dir, h.hexdigest())
    f = open(filename, 'w')
    f.close()


def locate_checkpoint(inputs, msg):
    """
    This checks if a message has already been indexed by using a digest of the first 300 characters,
    which includes a date, message id, source and destination email addresses.
    :param inputs: contains the input definition which includes the path to its checkpoint directory
     :type inputs: InputDefinition
    :param msg: Contains a message that needs to indexed and
     :type msg: basestring
    :return: Returns true if the message has been indexed previously, and false if not.
     :rtype: bool
    """
    h = hashlib.new('sha256')
    h.update(msg[0:300])
    checkpoint_dir = inputs.metadata['checkpoint_dir']
    filename = os.path.join(checkpoint_dir, h.hexdigest())
    try:
        open(filename, 'r').close()
    except (OSError, IOError):
        return False
    return True
