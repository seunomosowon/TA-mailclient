"""This contains exceptions defined for the Mail scheme"""


from urllib2 import HTTPError
from ssl import SSLError


class MailException(Exception):
    """
    Exception raised for errors in the mail modular input.
    """


class MailExceptionInvalidProtocol(MailException):
    """
    Raised if an invalid mail protocol is defined.
    This requires POP3 or IMAP
    """

    def __init__(self):
        MailException.__init__(self, 'protocol must be set to either POP3 or IMAP')


class MailExceptionStanzaNotEmail(MailException):
    """
    Raised if the stanza is not an email address
    """

    def __init__(self, message):
        self.input = message
        MailException.__init__(self, 'Input stanza must be an email address. Error parsing %s' % message)


class MailProtocolError(MailException):
    """
    Raised when a Poplib exception is thrown and caught
    """

    def __init__(self, message):
        self.message = message
        MailException.__init__(self, 'Exception thrown by Poplib or Imaplib, %s' % message)


class MailConnectionError(MailException):
    """
    Raised when there's a connection error
    """

    def __init__(self, message):
        self.message = message
        MailException.__init__(self, 'Mail connection error: %s' % message)


class MailLoginFailed(MailException):
    """
    Raised when there's a login failure
    """

    def __init__(self, server, username):
        self.user = username
        MailException.__init__(self, 'Login failed on %s for username: %s' % (server, username))


