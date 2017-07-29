import imaplib
from .mail_common import *


def stream_imap_emails(server, is_secure, credential, checkpoint_dir,
                       mailbox_mgmt=MAILBOX_CLEANUP_DEFAULTS, include_headers=INDEX_ATTACHMENT_DEFAULT):
    """
    This fetches a maximum of MAX_FETCH_COUNT mails using imap form a mail server.
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
    :param include_headers: This parameter specifies if all headers should be included. (default)
    :type include_headers: bool
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
        raise MailLoginFailed(server, credential.username)
    except (socket.error, SSLError) as e:
        raise MailConnectionError(e)
    mailclient.list()
    if mailbox_mgmt == 'delete' or mailbox_mgmt == 'delayed':
        imap_readonly_flag = False
    else:
        imap_readonly_flag = IMAP_READONLY_FLAG
    """
    Might want to iterate over all the child folders of inbox in future version
    And Extend the choise of having this readonly, so mails are saved in mailbox.
    Need to move all this into a controller object that can work on email.Message.Message
    """
    mailclient.select('inbox', readonly=imap_readonly_flag)
    status, data = mailclient.uid('search', None, 'ALL')
    if status == 'OK':
        email_ids = data[0].split()
        num_of_messages = len(email_ids)
        if num_of_messages > 0:
            num = 0
            mails_retrieved = 0
            while mails_retrieved < MAX_FETCH_COUNT and num != num_of_messages:
                result, email_data = mailclient.uid('fetch', email_ids[num], '(RFC822)')
                raw_email = email_data[0][1]
                formatted_email = process_raw_email(raw_email, include_headers)
                email_id = formatted_email[1]
                if locate_checkpoint(checkpoint_dir, email_id) and (
                        mailbox_mgmt == 'delayed' or mailbox_mgmt == 'delete'):
                    mailclient.uid('store', email_ids[num], '+FLAGS', '(\\Deleted)')
                    # if not locate_checkpoint(...): then message deletion has been delayed until next run
                else:
                    fetched_mail.append(formatted_email)
                    mails_retrieved += 1
                if mailbox_mgmt == 'delete':
                    mailclient.uid('store', email_ids[num], '+FLAGS', '(\\Deleted)')
                num += 1
            mailclient.expunge()
            mailclient.close()
            mailclient.logout()
    return fetched_mail
