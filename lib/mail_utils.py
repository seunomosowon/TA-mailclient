from __future__ import unicode_literals

from six import text_type, binary_type

import hashlib
import os
import socket
import re


def mail_connectivity_test(server, protocol):
    """
    This validates connectivity to given hostname and port
    :param server: This is the remote hostname or IP to be used for the test.
    :type server: basestring
    :param protocol: The protocol to be used to fetch emails - IMAPS or POP3S
    :type protocol: basestring
    :return: Raises an exception back to the modinput validation if connectivity test fails
    """
    try:
        captive_dns_addr = socket.gethostbyname(server)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((captive_dns_addr, get_mail_port(protocol=protocol)))
        s.close()
    except socket.error as e:
        raise socket.error("Socket error : %s" % e)


def save_checkpoint(checkpoint_dir, msg):
    """
    This creates a checkpoint file in the checkpoint directory for the message.
    :param checkpoint_dir: This contains the path where checkpoint files will be saved
    :type checkpoint_dir: basestring
    :param msg: Contains a message that needs to indexed and
     :type msg: basestring
    """
    filename = os.path.join(checkpoint_dir, hashlib.sha256(msg.encode("utf8", "backslashreplace")).hexdigest())
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
    filename = os.path.join(checkpoint_dir, hashlib.sha256(msg.encode("utf8", "backslashreplace")).hexdigest())
    try:
        open(filename, 'r').close()
    except (OSError, IOError):
        return False
    return True


def bool_variable(x):
    """

    :param x: variable to be converted to boolean. This defaults to true if unsupported values are passed to this
    :return:
    """
    if x == "enabled":
        x = True
    elif x == "disabled":
        x = False
    elif x == "True":
        x = True
    elif x == "False":
        x = False
    elif x == "1" or x == "0":
        x = bool(int(x))
    else:
        x = True
    return x


def get_mail_port(protocol):
    """
    This returns the server port to use for POP retrieval of mails
    :param protocol: The protocol to be used to fetch emails - IMAP or POP3
    :type protocol: basestring
    :return: Returns the correct port for either POP3 or POP3 over SSL
    :rtype: int
    """
    if protocol == 'POP3':
        port = 995
    elif 'IMAP' == protocol:
        port = 993
    else:
        raise Exception("Invalid options passed to get_mail_port")
    return port

def drop_attachment_from_event(message):
    """
    This prevent the attachment content to be ingested in clear text by
    dropping its content. If attachment is unsupported, nothing done.
    :param message: Email message to be ingested as event in Splunk
    :type message: basestring
    :return: Return the email message with no attachment content
    :rtype: basestring
    """
    pattern = r'^#BEGIN_ATTACHMENT:\s(.*)#END_ATTACHMENT:\s'
    return re.sub(pattern, "", message, flags=re.DOTALL|re.MULTILINE)