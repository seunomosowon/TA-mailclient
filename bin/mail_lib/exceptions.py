"""This contains exceptions defined for the Mail scheme"""


class MailException(Exception):
    """
    Exception raised for errors in the mail modular input.
    """


class MailExceptionInputError(MailException):
    """
    Raised if there is a problem in the input name.
    E.g if the input_name read is not in the form kind://stanza
    """
    def __init__(self, message):
        self.input = message
        MailException.__init__(self, 'Problem parsing input, %s' % message)


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


class MailPoplibError(MailException):
    """
    Raised when a Poplib exception is thrown and caught
    """
    def __init__(self, message):
        self.message = message
        MailException.__init__(self, 'Exception thrown by Poplib, %s' % message)


class MailExceptionIMAPLogin(MailException):
    """
    Raised when login fails using IMAP
    """
    def __init__(self, server, username, message):
        self.server = server
        self.username = username
        self.message = message
        MailException.__init__(self, 'IMAP Login failed to server,%s, for user, %s. %s' % (server, username, message))


class MailPasswordNotFound(MailException):
    """
    Raised when password is not found in Splunk
    """
    def __init__(self, username):
        self.user = username
        MailException.__init__(self, 'Mail password not found for email, %s' % username)


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

