[mail://<name>]
* The name of the stanza should be an email address which would be used to connect to the server.

protocol = [POP3|IMAP]
* The protocol to be used to fetch emails from the server

mailserver = <value>
* This is the mailserver to fetch mails from

password = <value>
* The password for the account provided in the stanza name

mailbox_cleanup = [delete,delayed,readonly]
* This determines if the mails should be one of the following:
 * delete: deleted as they are indexed
 * delayed: deleted on next connection to the mailbox after verifying that the mail was indexed
 * readonly: mails will not be deleted. It will be read and left in the mailbox.
* If this is not set, the default option used will be readonly

include_headers =  <bool>
* This determines if email headers should be included.

maintain_rfc =  <bool>
* This determines if email will still maintain RFC compatability for parsing tools

attach_message_primary =  <bool>
* This determines if an attached message will instead be the indexed email (assuming the outer message was just the delivery mechanism)

additional_folders = <value>
* This suggests additional folders to read messages via IMAP