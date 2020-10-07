from __future__ import unicode_literals

import hashlib
import os
import socket


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
    elif x is "1" or x is "0":
        x = bool(int(x))
    else:
        x = bool(int(1))
    return x


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
            raise Exception("Invalid options passed to get_mail_port")
    else:
        if protocol == 'POP3':
            port = 110
        elif protocol == 'IMAP':
            port = 143
        else:
            raise Exception("Invalid options passed to get_mail_port")
    return port
