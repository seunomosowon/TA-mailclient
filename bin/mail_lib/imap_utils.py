import imaplib
from mail_common import *
from constants import *
from exceptions import *


def stream_imap_emails(server, is_secure, credential):
    """
    This fetches a maximum of MAX_FETCH_COUNT mails using imap form a mail server
    :param server: mail server hostname or IP address
    :type server: basestring
    :param is_secure: true/false
    :type is_secure: bool
    :param credential: Pass a StoragePassword object to be used to access the server
    :type credential: StoragePassword
    :return: This returns a list of the messages retrieved via IMAP
    :rtype: list
    """
    # Define local variables
    fetched_mail = []
    if is_secure is True:
        mailclient = imaplib.IMAP4_SSL(server)
    else:
        mailclient = imaplib.IMAP4(server)
    try:
        mailclient.login(credential.username, credential.clear_password)
    except imaplib.IMAP4.error:
        raise MailExceptionIMAPLogin(server, credential.username)
    result, folders = mailclient.list()
    """Might want to iterate over all the child folders of inbox in future version
    And Extend the choise of having this readonly, so mails are saved in mailbox"""
    mailclient.select('inbox', readonly=False)
    status, data = mailclient.uid('search', None, 'ALL')
    if status == 'OK':
        email_ids = data[0].split()
        num_of_messages = len(email_ids)
        if num_of_messages > 0:
            if num_of_messages > MAX_FETCH_COUNT:
                fetch_count = MAX_FETCH_COUNT
            else:
                fetch_count = num_of_messages
            for num in range(fetch_count):
                result, email_data = mailclient.uid('fetch', email_ids[num], '(RFC822)')
                raw_email = email_data[0][1]
                fetched_mail.append(process_raw_email(raw_email))
                mailclient.uid('store', email_ids[num], '+FLAGS', '(\\Deleted)')
            mailclient.expunge()
            mailclient.close()
            mailclient.logout()
    return fetched_mail
