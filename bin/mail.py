#!/opt/splunk/bin/python

from __future__ import unicode_literals

import imaplib
import poplib
# import libraries required
import re
import os
import sys
import traceback
from ssl import SSLError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from mail_constants import *
from mail_exceptions import *
from mail_utils import *
from file_parser import *
from splunklib.modularinput import *
from six import ensure_str

# Define global variables
__author__ = 'seunomosowon'


class Mail(Script):
    """This inherits the class Script from the splunklib.modularinput script
    They must override the get_scheme and stream_events functions, and,
    if the scheme returned by get_scheme has Scheme.use_external_validation
    set to True, the validate_input function.
    """
    APP = __file__.split(os.sep)[-3]

    def __init__(self):
        super(Mail, self).__init__()
        self.realm = REALM
        self.log = EventWriter.log
        self.write_event = EventWriter.write_event
        self.checkpoint_dir = ""

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
        maintain_rfc = Argument(
            name="maintain_rfc",
            title="Maintain RFC compatability",
            validation="is_bool('maintain_rfc')",
            data_type=Argument.data_type_boolean,
            required_on_edit=False,
            required_on_create=False
        )
        scheme.add_argument(maintain_rfc)
        attach_message_primary = Argument(
            name="attach_message_primary",
            title="Attached messages become primary",
            validation="is_bool('attach_message_primary')",
            data_type=Argument.data_type_boolean,
            required_on_edit=False,
            required_on_create=False
        )
        scheme.add_argument(attach_message_primary)
        additional_folders = Argument(
            name="additional_folders",
            title="Additional folders",
            description="comma separated list",
            validation=".*",
            data_type=Argument.data_type_string,
            required_on_edit=False,
            required_on_create=False
        )
        scheme.add_argument(additional_folders)
        return scheme

    # noinspection PyShadowingNames
    def validate_input(self, validation_definition):
        """
        We are using external validation to check if the server is indeed a POP3 server.
        If validate_input does not raise an Exception, the input is assumed to be valid.
        """
        mailserver = validation_definition.parameters["mailserver"]
        protocol = validation_definition.parameters["protocol"]
        email_address = validation_definition.metadata["name"]
        match = re.match(REGEX_EMAIL, email_address)
        if not match:
            raise MailExceptionStanzaNotEmail(email_address)
        mail_connectivity_test(server=mailserver, protocol=protocol)

    def mask_input_password(self):
        """
        This encrypts the password stored in inputs.conf for the input name passed as an argument.
        """
        kwargs = dict(host=self.mailserver, password=PASSWORD_PLACEHOLDER, mailserver=self.mailserver,
                      protocol=self.protocol, mailbox_cleanup=self.mailbox_cleanup,
                      include_headers=self.include_headers, maintain_rfc=self.maintain_rfc,
                      attach_message_primary=self.attach_message_primary)
        try:
            self.service.inputs[self.username].update(**kwargs).refresh()
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
        mailclient = imaplib.IMAP4_SSL(self.mailserver)
        try:
            # mailclient.debug = 4
            self.log(EventWriter.INFO, "IMAP - Connecting to mailbox as %s" % self.username)
            mailclient.login(credential.username, credential.clear_password)
        except imaplib.IMAP4.error:
            raise MailLoginFailed(self.mailserver, credential.username)
        except (socket.error, SSLError) as e:
            raise MailConnectionError(e)
        self.log(EventWriter.INFO, "Listing folders in mailbox=%s" % self.username)
        # with Capturing() as output:
        status, imap_list = mailclient.list()
        if status == 'OK':
            mail_folder_list = [ensure_str(each_folder).split('"')[-2] for each_folder in imap_list]
            folders = ','.join(mail_folder_list)
            self.log(EventWriter.INFO, "Folders found: {}".format(folders))
        if self.mailbox_cleanup == 'delete' or self.mailbox_cleanup == 'delayed':
            imap_readonly_flag = False
        else:
            self.log(EventWriter.INFO, "Accessing mailbox with readonly attribute")
            imap_readonly_flag = IMAP_READONLY_FLAG
        # if not self.read_inbox: folder_list = [], else: folder_list = ['inbox']
        folder_list = ['inbox']
        folder_list.extend(self.additional_folders)
        for each_folder in folder_list:
            mailclient.select(each_folder, readonly=imap_readonly_flag)
            status, data = mailclient.uid('search', None, 'ALL')
            mails_retrieved = 0
            if status == 'OK':
                email_ids = data[0].split()
                num_of_messages = len(email_ids)
                if num_of_messages > 0:
                    num = 0
                    while num != num_of_messages:
                        result, email_data = mailclient.uid('fetch', email_ids[num], '(RFC822)')
                        if result == 'OK':
                            raw_email = email_data[0][1]
                            raw_email = raw_email.decode("ascii", "replace")
                            message_time, message_mid, msg = email_mime.parse_email(
                                raw_email,
                                self.include_headers,
                                self.maintain_rfc,
                                self.attach_message_primary,
                            )
                            if locate_checkpoint(self.checkpoint_dir, message_mid) and (
                                    self.mailbox_cleanup == 'delayed' or self.mailbox_cleanup == 'delete'):
                                mailclient.uid('store', email_ids[num], '+FLAGS', '(\\Deleted)')
                                mailclient.expunge()
                                self.log(EventWriter.DEBUG, "Mail already indexed: %s" % message_mid)
                                # if not locate_checkpoint(...): then message deletion has been delayed until next run
                            elif not locate_checkpoint(self.checkpoint_dir, message_mid):
                                logevent = Event(
                                    stanza=self.username,
                                    data=msg,
                                    host=self.mailserver,
                                    source="{}/{}".format(self.input_name, each_folder),
                                    time="%.3f" % message_time,
                                    done=True,
                                    unbroken=True
                                )
                                self.write_event(logevent)
                                save_checkpoint(self.checkpoint_dir, message_mid)
                                mails_retrieved += 1
                            if self.mailbox_cleanup == 'delete':
                                mailclient.uid('store', email_ids[num], '+FLAGS', '(\\Deleted)')
                                mailclient.expunge()
                        num += 1
            self.log(EventWriter.INFO,
                     "Retrieved %d mails from mailbox: %s/%s" % (mails_retrieved, self.username, each_folder))

        mailclient.close()
        mailclient.logout()

    def stream_pop_emails(self):
        """
        :return: This returns a list of the messages retrieved via POP3
        :rtype: list
        """
        credential = self.get_credential()
        try:
            mailclient = poplib.POP3_SSL(host=self.mailserver)
        except (socket.error, SSLError) as e:
            raise MailConnectionError(e)
        except poplib.error_proto as e:
            """Some kind of poplib exception: EOF or other"""
            raise MailProtocolError(str(e))
        try:
            mailclient.set_debuglevel(2)
            self.log(EventWriter.INFO, "POP3 - Connecting to mailbox as %s" % self.username)
            self.log(EventWriter.INFO, "POP3 debug: %s" % mailclient.user(credential.username))
            mailclient.set_debuglevel(1)
            self.log(EventWriter.INFO, "POP3 debug: %s" % mailclient.pass_(credential.clear_password))
        except poplib.error_proto:
            raise MailLoginFailed(self.mailserver, credential.username)
        num = 0
        mails_retrieved = 0
        (num_of_messages, totalsize) = mailclient.stat()
        if num_of_messages > 0:
            while num != num_of_messages:
                num += 1
                (header, lines, octets) = mailclient.retr(num)
                # raw_email = '\n'.join(lines)
                raw_email = b'\n'.join(lines).decode('utf-8')
                message_time, message_mid, msg = email_mime.parse_email(
                    raw_email,
                    self.include_headers,
                    self.maintain_rfc,
                    self.attach_message_primary,
                )
                if not locate_checkpoint(self.checkpoint_dir, message_mid):
                    """index the mail if it is readonly or if the mail will be deleted"""
                    logevent = Event(
                        stanza=self.username,
                        data=msg,
                        host=self.mailserver,
                        source=self.input_name,
                        time="%.3f" % message_time,
                        done=True,
                        unbroken=True
                    )
                    self.write_event(logevent)
                    save_checkpoint(self.checkpoint_dir, message_mid)
                    mails_retrieved += 1
                    if self.mailbox_cleanup == 'delete':
                        mailclient.dele(num)
                elif locate_checkpoint(self.checkpoint_dir, message_mid) and (
                        self.mailbox_cleanup == 'delayed' or self.mailbox_cleanup == 'delete'):
                    self.log(EventWriter.DEBUG, "Found a mail that had already been indexed: %s" % message_mid)
                    mailclient.dele(num)
            mailclient.quit()
            self.log(EventWriter.INFO, "Retrieved %d mails from mailbox: %s" % (mails_retrieved, self.username))

    def stream_events(self, inputs, ew):
        try:
            self._stream_events(inputs, ew)
        except Exception as e:
            self.log(EventWriter.ERROR, "Top level exception:  %s\n%s" % (e, traceback.format_exc()))

    def _stream_events(self, inputs, ew):
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
        self.log = ew.log
        self.write_event = ew.write_event
        input_list = inputs.inputs.popitem()
        """This runs just once since the default self.use_single_instance = False"""
        input_name, input_item = input_list
        self.input_name = input_name
        self.mailserver = input_item["mailserver"]
        self.username = input_name.split("://")[1]
        self.password = input_item["password"]
        self.protocol = input_item['protocol']
        # Optional Parameters
        if 'additional_folders' in input_item.keys():
            self.additional_folders = input_item['additional_folders'].split(',')
        else:
            self.additional_folders = []
        if 'include_headers' in input_item.keys():
            self.include_headers = bool_variable(input_item['include_headers'])
        else:
            self.include_headers = DEFAULT_INCLUDE_HEADERS
        if 'maintain_rfc' in input_item.keys():
            self.maintain_rfc = bool_variable(input_item['maintain_rfc'])
        else:
            self.maintain_rfc = DEFAULT_MAINTAIN_RFC
        if 'attach_message_primary' in input_item.keys():
            self.attach_message_primary = bool_variable(input_item['attach_message_primary'])
        else:
            self.attach_message_primary = DEFAULT_ATTACH_MESSAGE_PRIMARY
        if 'mailbox_cleanup' in input_item.keys():
            self.mailbox_cleanup = input_item['mailbox_cleanup']
        else:
            self.mailbox_cleanup = DEFAULT_MAILBOX_CLEANUP
        self.checkpoint_dir = inputs.metadata['checkpoint_dir']
        match = re.match(REGEX_EMAIL, self.username)
        if not match:
            ew.log(EventWriter.ERROR, "Modular input name must be an email address")
            self.disable_input()
            raise MailExceptionStanzaNotEmail(self.username)
        self.save_password()
        if "POP3" == self.protocol:
            self.stream_pop_emails()
        elif "IMAP" == self.protocol:
            self.stream_imap_emails()
        else:
            ew.log(EventWriter.ERROR, "Protocol must be either POP3 or IMAP")
            self.disable_input()
            raise MailExceptionInvalidProtocol


if __name__ == "__main__":
    sys.exit(Mail().run(sys.argv))
