#!/opt/splunk/bin/python

# import libraries required
import re
import traceback

from mail_lib.imap_utils import *
from mail_lib.pop_utils import *
from splunklib.modularinput import *
import sys


# Define global variables
__author__ = 'seunomosowon'


class Mail(Script):
    """This inherits the class Script from the splunklib.modularinput script
    They must override the get_scheme and stream_events functions, and,
    if the scheme returned by get_scheme has Scheme.use_external_validation
    set to True, the validate_input function.
    """
    APP = __file__.split(os.sep)[-3]

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

    def validate_input(self, validation_definition):
        """
        We are using external validation to check if the server is indeed a POP3 server.
        If validate_input does not raise an Exception, the input is assumed to be valid.
        """
        mailserver = validation_definition.parameters["mailserver"]
        is_secure = bool(validation_definition.parameters["is_secure"])
        protocol = validation_definition.parameters["protocol"]
        email_address = validation_definition.metadata["name"]
        match = re.match(REGEX_EMAIL, email_address)
        if match is None:
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
        if cred is not None:
            if self.password == PASSWORD_PLACEHOLDER:
                """Already encrypted"""
                return cred
            else:
                """Update password"""
                self.delete_password()
                cred = self.encrypt_password()
                self.mask_input_password()
                return cred
        else:
            if self.password == PASSWORD_PLACEHOLDER or self.password is None:
                raise Exception("Password cannot be empty or : %s" % PASSWORD_PLACEHOLDER)
            else:
                cred = self.encrypt_password()
                self.mask_input_password()
                return cred

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
            is_secure = bool(input_item["is_secure"])
            protocol = input_item['protocol']
            mailbox_cleanup = input_item['mailbox_cleanup']
            include_headers = bool(input_item['include_headers'])
            checkpoint_dir = inputs.metadata['checkpoint_dir']
            match = re.match(REGEX_EMAIL, str(self.username))
            if match is None:
                ew.log(EventWriter.ERROR, "Modular input name must be an email address")
                self.disable_input()
                raise MailExceptionStanzaNotEmail(self.username)
            if mailbox_cleanup is None or mailbox_cleanup == '':
                mailbox_cleanup = MAILBOX_CLEANUP_DEFAULTS
            sp = self.save_password()
            if "POP3" == protocol:
                mail_list = stream_pop_emails(
                    server=self.mailserver, is_secure=is_secure, credential=sp, checkpoint_dir=checkpoint_dir,
                    mailbox_mgmt=mailbox_cleanup, include_headers=include_headers)
            elif "IMAP" == protocol:
                mail_list = stream_imap_emails(
                    server=self.mailserver, is_secure=is_secure, credential=sp, checkpoint_dir=checkpoint_dir,
                    mailbox_mgmt=mailbox_cleanup, include_headers=include_headers)
            else:
                ew.log(EventWriter.DEBUG, "Protocol must be either POP3 or IMAP")
                self.disable_input()
                raise MailExceptionInvalidProtocol
            """Consider adding a checkpoint file here using the first n-characters including the date"""
            for message_time, checkpoint_id, msg in mail_list:
                if not locate_checkpoint(checkpoint_dir, checkpoint_id):
                    logevent = Event(
                        stanza=self.input_name,
                        data=msg,
                        host=self.mailserver,
                        source=self.input_name,
                        time="%.3f" % message_time
                    )
                    ew.write_event(logevent)
                    save_checkpoint(checkpoint_dir, checkpoint_id)
                else:
                    ew.log(EventWriter.DEBUG, "Found a mail that had already been indexed")
        except MailException as e:
            ew.log(EventWriter.INFO, str(e))
        except HTTPError:
            """Catch most exceptions from the sdk - usually due to permissions"""
            exc_type, exc_value, exc_traceback = sys.exc_info()
            ew.log(EventWriter.DEBUG, repr(traceback.format_tb(exc_traceback)))
            ew.log(EventWriter.DEBUG, "*** traceback_lineno: %s" % exc_traceback.tb_lineno)
            ew.log(EventWriter.DEBUG,
                   traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout))


if __name__ == "__main__":
    sys.exit(Mail().run(sys.argv))
