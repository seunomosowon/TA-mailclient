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

from .mail_common import *


def stream_pop_emails(server, is_secure, credential, checkpoint_dir,
                      mailbox_mgmt=MAILBOX_CLEANUP_DEFAULTS, include_headers=INDEX_ATTACHMENT_DEFAULT):
    """
    :param server: mail server hostname or IP address
    :type server: basestring
    :param is_secure: true/false
    :type is_secure: bool
    :param credential: Pass a StoragePassword object to be used to access the server
    :type credential: StoragePassword
    :param mailbox_mgmt: This dictates if mail deletion should be deferred, enforced as mails are indexed or avoided
    :type mailbox_mgmt: basestring
    :param checkpoint_dir: This is the path to be checked for existing checkpoint files
    :type checkpoint_dir: basestring
    :param include_headers: This parameter specifies if all headers should be included.
    :type include_headers: bool
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
    except (socket.error, SSLError) as e:
        raise MailConnectionError(e)
    except poplib.error_proto, e:
        """Some kind of poplib exception: EOF or other"""
        raise MailProtocolError(str(e))
    try:
        mailclient.user(credential.username)
        mailclient.pass_(credential.clear_password)
    except poplib.error_proto:
        raise MailLoginFailed(server, credential.username)
    (num_of_messages, totalsize) = mailclient.stat()
    if num_of_messages > 0:
        num = 0
        mails_retrieved = 0
        while mails_retrieved < MAX_FETCH_COUNT and num != num_of_messages:
            num += 1
            (header, msg, octets) = mailclient.retr(num)
            # fetched_mail.append(header + '\n'.join(msg))
            raw_email = '\n'.join(msg)
            formatted_email = process_raw_email(raw_email, include_headers)
            email_id = formatted_email[1]
            if not locate_checkpoint(checkpoint_dir, email_id):
                """Append the mail if it is readonly or if the mail will be deleted"""
                fetched_mail.append(formatted_email)
                mails_retrieved += 1
                if mailbox_mgmt == 'delete':
                    mailclient.dele(num)
            elif locate_checkpoint(checkpoint_dir, email_id) and (
                    mailbox_mgmt == 'delayed' or mailbox_mgmt == 'delete'):
                mailclient.dele(num)
        mailclient.quit()
    return fetched_mail
