#!/opt/splunk/bin/python

# import libraries required
import re
from ssl import SSLError
from splunklib.modularinput import *
import sys
import poplib
import imaplib
from mail_lib.mail_common import *

# Define global variables
__author__ = 'seunomosowon'


class Mail(Script):
    """This inherits the class Script from the splunklib.modularinput script
    They must override the get_scheme and stream_events functions, and,
    if the scheme returned by get_scheme has Scheme.use_external_validation
    set to True, the validate_input function.
    """
    APP = __file__.split(os.sep)[-3]

    # noinspection PyShadowingNames
    def get_scheme(self):
        """This overrides the super method from the parent class"""
        scheme = Scheme("Mail Server")
        scheme.description = "Streams events from from a mail server."
        scheme.use_external_validation = True
        name = Argument(
            name="name",
            title="E-mail",
            description="Enter E-mail Address",
            validation="match('name','%s')" % REGEX_EMAIL,
            data_type=Argument.data_type_string,
            required_on_edit=True,
            required_on_create=True
        )
        scheme.add_argument(name)
        protocol = Argument(
            name="protocol",
            title="Protocol",
            description="Collection Protocol (POP3/IMAP)",
            validation="match('protocol','^(POP3|IMAP)$')",
            data_type=Argument.data_type_string,
            required_on_edit=True,
            required_on_create=True
        )
        scheme.add_argument(protocol)
        mailserver = Argument(
            name="mailserver",
            title="Server",
            description="Mail Server (hostname or IP)",
            validation="match('mailserver','%s')" % REGEX_HOSTNAME,
            data_type=Argument.data_type_string,
            required_on_edit=True,
            required_on_create=True
        )
        scheme.add_argument(mailserver)
        is_secure = Argument(
            name="is_secure",
            title="UseSSL",
            description="Enable Protocol over SSL",
            validation="is_bool('is_secure')",
            data_type=Argument.data_type_boolean,
            required_on_edit=True,
            required_on_create=True
        )
        # bool arguments dont display description
        scheme.add_argument(is_secure)
        password = Argument(
            name="password",
            title="Account Password",
            description="Enter Password for mail account",
            data_type=Argument.data_type_string,
            required_on_edit=True,
            required_on_create=True
        )
        # validation="match('password','%s')" % REGEX_PASSWORD,
        scheme.add_argument(password)
        mailbox_cleanup = Argument(
            name="mailbox_cleanup",
            title="Maibox Management",
            description="(delete|delayed|readonly)",
            validation="match('mailbox_cleanup','^(delete|delayed|readonly)$')",
            data_type=Argument.data_type_string,
            required_on_edit=False,
            required_on_create=False
        )
        scheme.add_argument(mailbox_cleanup)
        include_headers = Argument(
            name="include_headers",
            title="Include headers",
            validation="is_bool('include_headers')",
            data_type=Argument.data_type_boolean,
            required_on_edit=False,
            required_on_create=False
        )
        scheme.add_argument(include_headers)
        return scheme

    # noinspection PyShadowingNames
    def validate_input(self, validation_definition):
        """
        We are using external validation to check if the server is indeed a POP3 server.
        If validate_input does not raise an Exception, the input is assumed to be valid.
        """
        mailserver = validation_definition.parameters["mailserver"]
        is_secure = bool(int(validation_definition.parameters["is_secure"]))
        include_headers = bool(int(validation_definition.parameters['include_headers']))
        protocol = validation_definition.parameters["protocol"]
        email_address = validation_definition.metadata["name"]
        match = re.match(REGEX_EMAIL, email_address)
        if not match:
            raise MailExceptionStanzaNotEmail(email_address)
        mail_connectivity_test(server=mailserver, protocol=protocol, is_secure=is_secure)

    def mask_input_password(self):
        """
        This encrypts the password stored in inputs.conf for the input name passed as an argument.
        """
        tmp_input = self.service.inputs[self.username]
        kwargs = dict(host=tmp_input.mailserver, password=PASSWORD_PLACEHOLDER, mailserver=tmp_input.mailserver,
                      is_secure=tmp_input.is_secure, protocol=tmp_input.protocol,
                      mailbox_cleanup=tmp_input.mailbox_cleanup, include_headers=tmp_input.include_headers)
        try:
            tmp_input.update(**kwargs).refresh()
        except Exception, e:
            self.disable_input()
            raise Exception("Error updating inputs.conf - %s" % e)

    def get_credential(self):
        """
        This encrypts the password stored in inputs.conf for the input name passed as an argument.
        :return: Returns the input with the encrypted password
        :rtype: StoragePassword
        """
        storagepasswords = self.service.storage_passwords
        if storagepasswords is not None:
            for credential_entity in storagepasswords:
                """ Use password in storage endpoint if realm matches """
                if credential_entity.username == self.username and credential_entity.realm == self.realm:
                    return credential_entity
        else:
            return None

    def encrypt_password(self):
        """
        This encrypts the password stored in inputs.conf for the input name passed as an argument.
        :return: Returns the input with the encrypted password
        :rtype: StoragePassword
        """
        storagepasswords = self.service.storage_passwords
        try:
            sp = storagepasswords.create(password=self.password, username=self.username, realm=self.realm)
        except Exception, e:
            self.disable_input()
            raise Exception("Could not create password entry {%s:%s} in passwords.conf: %s" % (
                self.username, self.realm, e))
        return sp

    def delete_password(self):
        """
        This deletes the password stored in inputs.conf for the input name passed as an argument.
        """
        try:
            self.service.storage_passwords.delete(self.username, self.realm)
        except Exception, e:
            self.disable_input()
            raise Exception("Could not delete credential {%s:%s} from passwords.conf: %s" % (
                self.username, self.realm, e))

    def disable_input(self):
        """
        This disables a modular input given the input name.
        :return: Returns the disabled input
        :rtype: Entity
        """
        self.service.inputs[self.username].disable()

    def save_password(self):
        """
        :return: This returns a StoragePassword with the right credentials,
                    after saving or updating the storage/passwords endpoint
         :rtype: StoragePassword
        """
        cred = self.get_credential()
        if cred:
            if self.password == PASSWORD_PLACEHOLDER:
                """Already encrypted"""
                return cred
            elif self.password:
                """Update password"""
                self.delete_password()
                cred = self.encrypt_password()
                self.mask_input_password()
                return cred
            else:
                raise Exception("Password cannot be empty")
        else:
            if self.password == PASSWORD_PLACEHOLDER or self.password is None:
                raise Exception("Password cannot be empty or : %s" % PASSWORD_PLACEHOLDER)
            else:
                cred = self.encrypt_password()
                self.mask_input_password()
                return cred

    def stream_imap_emails(self):
        """
        :return: This returns a list of the messages retrieved via IMAP
        :rtype: list
        """
        # Define local variables
        credential = self.get_credential()
        fetched_mail = []

        if self.is_secure is True:
            mailclient = imaplib.IMAP4_SSL(self.mailserver)
        else:
            mailclient = imaplib.IMAP4(self.mailserver)
        try:
            mailclient.login(credential.username, credential.clear_password)
        except imaplib.IMAP4.error:
            raise MailLoginFailed(self.mailserver, credential.username)
        except (socket.error, SSLError) as e:
            raise MailConnectionError(e)
        mailclient.list()
        if self.mailbox_cleanup == 'delete' or self.mailbox_cleanup == 'delayed':
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
                    formatted_email = process_raw_email(raw_email, self.include_headers)
                    mid = formatted_email[1]
                    if locate_checkpoint(self.checkpoint_dir, mid) and (
                                    self.mailbox_cleanup == 'delayed' or self.mailbox_cleanup == 'delete'):
                        mailclient.uid('store', email_ids[num], '+FLAGS', '(\\Deleted)')
                        # if not locate_checkpoint(...): then message deletion has been delayed until next run
                    else:
                        fetched_mail.append(formatted_email)
                        mails_retrieved += 1
                    if self.mailbox_cleanup == 'delete':
                        mailclient.uid('store', email_ids[num], '+FLAGS', '(\\Deleted)')
                    num += 1
                mailclient.expunge()
                mailclient.close()
                mailclient.logout()
        return fetched_mail

    def stream_pop_emails(self):
        """
        :return: This returns a list of the messages retrieved via POP3
        :rtype: list
        """
        fetched_mail = []
        credential = self.get_credential()
        try:
            if self.is_secure:
                mailclient = poplib.POP3_SSL(host=self.mailserver,
                                             port=get_mail_port(protocol=self.protocol, is_secure=self.is_secure))
            else:
                mailclient = poplib.POP3(host=self.mailserver,
                                         port=get_mail_port(protocol=self.protocol, is_secure=self.is_secure))
        except (socket.error, SSLError) as e:
            raise MailConnectionError(e)
        except poplib.error_proto, e:
            """Some kind of poplib exception: EOF or other"""
            raise MailProtocolError(str(e))
        try:
            mailclient.set_debuglevel(2)
            self.log(EventWriter.INFO, "Connecting to mailbox as %s" % self.username)
            self.log(EventWriter.INFO, mailclient.user(credential.username))
            self.log(EventWriter.INFO, mailclient.pass_(credential.clear_password))
        except poplib.error_proto:
            raise MailLoginFailed(self.mailserver, credential.username)
        (num_of_messages, totalsize) = mailclient.stat()
        if num_of_messages > 0:
            num = 0
            mails_retrieved = 0
            while mails_retrieved < MAX_FETCH_COUNT and num != num_of_messages:
                num += 1
                (header, msg, octets) = mailclient.retr(num)
                raw_email = '\n'.join(msg)
                formatted_email = process_raw_email(raw_email, self.include_headers)
                mid = formatted_email[1]
                if not locate_checkpoint(self.checkpoint_dir, mid):
                    """Append the mail if it is readonly or if the mail will be deleted"""
                    fetched_mail.append(formatted_email)
                    mails_retrieved += 1
                    if self.mailbox_cleanup == 'delete':
                        mailclient.dele(num)
                elif locate_checkpoint(self.checkpoint_dir, mid) and (
                                self.mailbox_cleanup == 'delayed' or self.mailbox_cleanup == 'delete'):
                    mailclient.dele(num)
            self.log(EventWriter.INFO, mailclient.quit())
        return fetched_mail

    def stream_events(self, inputs, ew):
        """This function handles all the action: splunk calls this modular input
        without arguments, streams XML describing the inputs to stdin, and waits
        for XML on stdout describing events.
        If you set use_single_instance to True on the scheme in get_scheme, it
        will pass all the instances of this input to a single instance of this
        script.
        :param inputs: an InputDefinition object
        :type inputs: InputDefinition
        :param ew: an EventWriter object
        :type ew: EventWriter
        """
        input_list = inputs.inputs.popitem()
        """This runs just once since the default self.use_single_instance = False"""
        try:
            input_name, input_item = input_list
            self.input_name = input_name
            self.mailserver = input_item["mailserver"]
            self.username = input_name.split("://")[1]
            self.password = input_item["password"]
            self.realm = REALM
            self.protocol = input_item['protocol']
            self.checkpoint_dir = inputs.metadata['checkpoint_dir']
            self.log = ew.log
            if not input_item['mailbox_cleanup']:
                self.mailbox_cleanup = input_item['mailbox_cleanup']
            if input_item['include_headers'] is not None:
                self.include_headers = bool(int(input_item['include_headers']))
            if input_item['is_secure'] is not None:
                self.is_secure = bool(int(input_item["is_secure"]))
            match = re.match(REGEX_EMAIL, str(self.username))
            if match is None:
                ew.log(EventWriter.ERROR, "Modular input name must be an email address")
                self.disable_input()
                raise MailExceptionStanzaNotEmail(self.username)
            self.save_password()
            if "POP3" == self.protocol:
                mail_list = self.stream_pop_emails()
            elif "IMAP" == self.protocol:
                mail_list = self.stream_imap_emails()
            else:
                ew.log(EventWriter.DEBUG, "Protocol must be either POP3 or IMAP")
                self.disable_input()
                raise MailExceptionInvalidProtocol
            """Consider adding a checkpoint file here using the first n-characters including the date"""
            for message_time, checkpoint_mid, msg in mail_list:
                if not locate_checkpoint(self.checkpoint_dir, checkpoint_mid):
                    logevent = Event(
                        stanza=self.input_name,
                        data=msg,
                        host=self.mailserver,
                        source=self.input_name,
                        time="%.3f" % message_time
                    )
                    ew.write_event(logevent)
                    save_checkpoint(self.checkpoint_dir, checkpoint_mid)
                else:
                    ew.log(EventWriter.DEBUG, "Found a mail that had already been indexed")
        except MailException as e:
            ew.log(EventWriter.INFO, str(e))

    def __init__(self):
        super(Mail, self).__init__()
        self.input_name = "xyz@abc.com"
        self.mailserver = "a.b.c.d"
        self.username = "xyz@abc.com"
        self.password = "xyz@abc.com"
        self.realm = REALM
        self.protocol = "POP3"
        self.checkpoint_dir = ""
        self.log = EventWriter.log
        self.include_headers = INDEX_ATTACHMENT_DEFAULT
        self.mailbox_cleanup = "readonly"
        self.is_secure = INDEX_ATTACHMENT_DEFAULT


if __name__ == "__main__":
    sys.exit(Mail().run(sys.argv))
