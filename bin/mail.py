#!/opt/splunk/bin/python

# import libraries required
import re
import sys
import time

from splunklib.modularinput import *
from mail_lib.imap_utils import *
from mail_lib.pop_utils import *
from mail_lib.constants import *
from mail_lib.mail_common import *
from mail_lib.exceptions import *

#
# Define global variables
__author__ = 'seunomosowon'


class Mail(Script):
    """This inherits the class Script from the splunklib.modularinput script
    They must override the get_scheme and stream_events functions, and,
    if the scheme returned by get_scheme has Scheme.use_external_validation
    set to True, the validate_input function.
    """
    def get_scheme(self):
        """This overrides the super method from the parent class"""
        scheme = Scheme("Mail Server")
        scheme.description = "Streams events from from a mail server."
        scheme.use_external_validation = True
        name = Argument(
            name="name",
            description="Email Address",
            validation="match('name','%s')" % REGEX_EMAIL,
            data_type=Argument.data_type_string,
            required_on_edit=True,
            required_on_create=True
        )
        scheme.add_argument(name)
        protocol = Argument(
            name="protocol",
            description="Collection Protocol (POP3/IMAP)",
            validation="match('protocol','^(POP3|IMAP)$')",
            data_type=Argument.data_type_string,
            required_on_edit=True,
            required_on_create=True
        )
        scheme.add_argument(protocol)
        mailserver = Argument(
                        name="mailserver",
                        description="POP3 Mail Server",
                        validation="match('mailserver','%s')" % REGEX_HOSTNAME,
                        data_type=Argument.data_type_string,
                        required_on_edit=True,
                        required_on_create=True
                        )
        scheme.add_argument(mailserver)
        is_secure = Argument(
                        name="is_secure",
                        description="Enable Protocol over SSL",
                        validation="is_bool('is_secure')",
                        data_type=Argument.data_type_boolean,
                        required_on_edit=True,
                        required_on_create=True
                        )
        scheme.add_argument(is_secure)
        password = Argument(
            name="password",
            description="Password",
            validation="match('password','%s')" % REGEX_PASSWORD,
            data_type=Argument.data_type_string,
            required_on_edit=True,
            required_on_create=True
        )
        scheme.add_argument(password)
        return scheme

    def validate_input(self, validation_definition):
        """
        We are using external validation to check if the server is indeed
        a POP3 server. If validate_input does not raise an Exception,
        the input is assumed to be valid.
        """
        mailserver = validation_definition.parameters["mailserver"]
        is_secure = bool(validation_definition.parameters["is_secure"])
        protocol = validation_definition.parameters["protocol"]
        email = validation_definition.metadata["name"]
        match = re.match(REGEX_EMAIL, email)
        if match is None:
            raise MailExceptionStanzaNotEmail(email)
        mail_connectivity_test(server=mailserver, protocol=protocol, is_secure=is_secure)

    def encrypt_input_password(self, input_name):
        """
        This encrypts the password stored in inputs.conf for the input name passed as an argument.
        :param input_name: Name of input that needs to be modified.
            This must be the input name just after the scheme - 'scheme://input_name_without_scheme'
        :type input_name: basestring
        :return: Returns the input with the encrypted password
        :rtype: Input
        """
        tmp_input = self.service.inputs[input_name]
        kwargs = {'host': tmp_input.mailserver, 'password': PASSWORD_PLACEHOLDER,
                  'mailserver': tmp_input.mailserver, 'is_secure': tmp_input.is_secure, 'protocol': tmp_input.protocol}
        tmp_input.update(**kwargs).refresh()

    def disable_input(self, input_name):
        """
        This disables a modular input given the input name.
        :param input_name: Name of input that needs to be disabled.
            This must be the input name just after the scheme - 'scheme://input_name_without_scheme'
        :type input_name: basestring
        :return: Returns the disabled input
        :rtype: Entity
        """
        self.service.inputs[input_name].disable()

    def save_password(self, username, input_list, ew):
        """
        :param username: Username to be saved or updated to Splunk endpoint, str or unicode
        :type username: basestring
        :param input_list: This is a list containing the input name and input settings for a single modular instance
        :type input_list: list
        :param ew: This is the event writer object that allows writing of logs or events
        :type ew: EventWriter
        :return: This returns a StoragePassword with the right credentials,
                    after saving or updating the storage/passwords endpoint
         :rtype: StoragePassword
        """
        input_name, input_item = input_list
        password = input_item['password']
        tmp_passwd = None
        match = re.match(REGEX_EMAIL, str(username))
        if match is not None:
            username = username
        else:
            ew.log(EventWriter.ERROR, "Modular input name must be an email address")
            self.disable_input(username)
            raise MailExceptionStanzaNotEmail(username)
        storagepasswords = self.service.storage_passwords
        if storagepasswords is not None:
            ew.log(EventWriter.DEBUG, "%d number of passwords found at endpoint" % (len(storagepasswords)))
            x = set()
            for credential_entity in storagepasswords:
                """ Use password in storage endpoint if realm matches """
                x.add(credential_entity.username)
                if credential_entity.username == username and credential_entity.realm == REALM:
                    tmp_passwd = credential_entity.clear_password
                    # can remove for loop - sp=credential_entity
                    ew.log(EventWriter.INFO,
                           "Got credentials from endpoint - Username(%s)" % username)
                else:
                    ew.log(EventWriter.DEBUG,
                           "User: %s, found in storage, did not match the email for this endpoint, %s" % (
                               credential_entity.username, username))
            if username in x and (password == PASSWORD_PLACEHOLDER or password is None) and tmp_passwd is not None:
                sp_in_list = [sp for sp in storagepasswords if sp.username == username and sp.realm == REALM]
                sp = sp_in_list[0]
            elif username in x and password != PASSWORD_PLACEHOLDER and password is not None:
                ew.log(EventWriter.INFO,
                       "Passwords updated. Updating storage")
                sp_in_list = [sp for sp in storagepasswords if sp.username == username and sp.realm == REALM]
                sp = sp_in_list[0]
                sp.update(**{'password': password}).refresh()
                ew.log(EventWriter.INFO, "Encrypting input password")
                self.encrypt_input_password(username)
            elif username not in x and password:
                ew.log(EventWriter.INFO,
                       "Password entity created - %s\%s." % (REALM, username))
                sp = storagepasswords.create(password=password, username=username, realm=REALM)
                self.encrypt_input_password(username)
                ew.log(EventWriter.DEBUG,
                       "Password obtained from inputs, and written to storage. Input (%s) updated with placeholder" % (
                           input_name))
            elif username not in x and not password:
                # raise Exception or just exit - Password not configured
                self.disable_input(username)
                raise MailPasswordNotFound(input_name)
        elif password is PASSWORD_PLACEHOLDER or password is None:
            ew.log(EventWriter.INFO,
                   "Password needs to be configured for the input before it's enabled and cannot be 'encrypted'")
            ew.log(EventWriter.INFO,
                   "No passwords found, disabling input")
            self.disable_input(username)
            raise MailPasswordNotFound(input_name)
        else:
            """
            Shouldnt reach here, I think I've captured most if not all possible outcomes above.
            If it does, then it's worth investigating here :)
            """
            ew.log(EventWriter.INFO, 'Password needs to be configured for the input before it is enabled'
                                     ' and cannot be \'encrypted\'')
            self.disable_input(username)
            raise MailPasswordNotFound(username)
        return sp

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
        for input_list in inputs.inputs.iteritems():
            """This runs just once since the default self.use_single_instance = False"""
            input_name, input_item = input_list
            mailserver = input_item["mailserver"]
            email = input_name.split("://")[1]
            is_secure = bool(input_item["is_secure"])
            protocol = input_item['protocol']
            sp = self.save_password(username=email, input_list=input_list, ew=ew)

            if "POP3" == protocol:
                mail_list = stream_pop_emails(server=mailserver, is_secure=is_secure, credential=sp)
            elif "IMAP" == protocol:
                mail_list = stream_imap_emails(server=mailserver, is_secure=is_secure, credential=sp)

            else:
                ew.log(EventWriter.DEBUG, "Protocol must be either POP3 or IMAP")
                self.disable_input(email)
                raise MailExceptionInvalidProtocol
            """Consider adding a checkpoint file here using the first n-characters including the date"""
            for message_time, msg in mail_list:
                if not locate_checkpoint(inputs, msg):
                    event = Event()
                    event.stanza = input_name
                    event.data = msg
                    event.time = "%.3f" % float(time.mktime(time.strptime(message_time[:(len(message_time)-6)],
                                                                          '%a, %d %b %Y %H:%M:%S')))
                    event.host = mailserver
                    ew.write_event(event)
                    save_checkpoint(inputs, msg)
                else:
                    ew.log(EventWriter.DEBUG, "Found a mail that had already been indexed")


if __name__ == "__main__":
    sys.exit(Mail().run(sys.argv))
