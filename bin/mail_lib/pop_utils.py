"""
Mail formats are different on each system and servers. Some header fields are added on arrival.

Here are some of the keys included in a sample mail from gmail to gmx:
['Return-Path', 'Received', 'Received', 'DKIM-Signature', 'X-Google-DKIM-Signature',
 'X-Gm-Message-State', 'X-Received', 'MIME-Version', 'Received', 'From', 'Date',
 'Message-ID', 'Subject', 'To', 'Content-Type', 'Envelope-To', 'X-GMX-Antispam',
  'X-GMX-Antivirus', 'X-UI-Filter results']
  This modular input has been cut down to only write out the basic header fields and mail body.
"""

import poplib
from mail_common import *
from constants import *
from exceptions import *


def stream_pop_emails(server, is_secure, credential):
    """
    :param server: mail server hostname or IP address
    :type server: basestring
    :param is_secure: true/false
    :type is_secure: bool
    :param credential: Pass a StoragePassword object to be used to access the server
    :type credential: StoragePassword
    :return: This returns a list of the messages retrieved via POP3
    :rtype: list
    """
    fetched_mail = []
    protocol = 'POP3'
    try:
        if is_secure is True:
            mailclient = poplib.POP3_SSL(host=server, port=get_mail_port(protocol=protocol, is_secure=is_secure))
        else:
            mailclient = poplib.POP3(host=server, port=get_mail_port(protocol=protocol, is_secure=is_secure))
        mailclient.user(credential.username)
        mailclient.pass_(credential.clear_password)
        (num_of_msgs, totalsize) = mailclient.stat()
        if num_of_msgs > 0:
            if num_of_msgs > MAX_FETCH_COUNT:
                fetch_count = MAX_FETCH_COUNT
            else:
                fetch_count = num_of_msgs

            for i in range(1, fetch_count + 1):
                (header, msg, octets) = mailclient.retr(i)
                # fetched_mail.append(header + '\n'.join(msg))
                raw_mail = '\n'.join(msg)
                fetched_mail.append(process_raw_email(raw_mail))
                mailclient.dele(i)

            mailclient.quit()

    except poplib.error_proto, e:
        raise MailPoplibError(e)

    return fetched_mail



