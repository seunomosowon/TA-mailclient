#Release Note
This technology adapter add-on fetches emails for Splunk to index from mailboxes
using either POP3 or IMAP, with or without SSL.

The modular input also stores takes the password from inputs.conf in plain text,
and replaces it with a place holder, while storing it encrypted within Splunk.
This is built using the Splunk SDK for Python,
should work on any Splunk installation with Python available including SHC.
Passwords should also get replicated between search heard peer members.

At present, this only fetches emails form the 'inbox' folder.
Images and attachments are not indexed.

Next update will allow the user add a list of Attachment extensions / content types to index.

###v0.2
* Adds support for base64 encoded emails.

###v0.3
* Adds support for mailbox cleanup options

###v0.4
* Added support for decoding unicode characters in other languages or and removing the unicode identifier in the header.
* Improved support for indexing some file types even if the content-type is not set correctly. (as with Microsoft sending some files as binaries instead of text)
* Added fundamental code to support indexing of attachment as a configurable option in future release by the user.
* Added multiple field extractions for the email header and file attachments.

**Note:** _filename_ and _filecontent_ are multi-valve fields.

**Faulty version** Introduced an error which was corrected in 0.4.1

###v0.4.1
Fixed bug with 0.4.0
* Made updates to fix unneeded else statement which introduced bug in 0.4.0.

###v0.4.2
* Added support for indexing mail headers


###v0.4.3
* Added support for indexing _.docx_ extensions
* Generalised ```Mail.save_password()``` to allow reuse of code
when writing other modular inputs.
* Optimized python import statements
* Fixed deleting of mails in poplib which was broken in 0.4

###v0.4.3
* Made extensions case insensitive

###v0.4.4
* Updated app to ignore case of file attachment extension 

###v0.4.5
* Fixed bug. Removed line which caused v0.4.4 to fail
* Fixed header inclusion

###v0.4.6
* Fixed bug. 
* Fixed header inclusion

###v0.4.7
* Removed password field validation to allow users have complex or easy passwords however long
* Handled all mail exceptions 

###v0.4.8
* removed error introduced in v0.4.7

###v0.4.9
* Changed encoding to support reading gmail.

###v0.5.0
* Fixed UTF-8 encoding of mails before indexing. (Supporting Gmail and others)

