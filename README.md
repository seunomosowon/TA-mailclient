# TA-mailclient

This technology adapter add-on fetches emails for Splunk to index from mailboxes
using either POP3 or IMAP, with or without SSL.

The modular input also stores takes the password from inputs.conf in plain text,
and replaces it with a place holder, while storing it encrypted within Splunk.
This is built using the Splunk SDK for Python,
should work on any Splunk installation with Python available including SHC.
Passwords should also get replicated between search heard peer members.

This only fetches emails form the 'inbox' folder for IMAP.

For multipart emails, only `'text/plain'` and `'text/html'` are indexed.
Images and attachments are not indexed.

Available at:

[Splunkbase](https://splunkbase.splunk.com/app/3200/#/details)

[Github](https://github.com/seunomosowon/TA-mailclient)


## Guide
This app adds a mail:// modular input and supports a variety of parameters.

```
[mail://email_address@domain.com]
interval = 600
is_secure = 1
mailserver = imap.domain.com
password = mypassword
protocol = IMAP|POP3
disabled = 0
```

Once the input is read, the password gets replaced and shows as 'encrypted'.
As such, the password for the mailbox must not be set to 'encrypted'.

The input can be edited if the password needs to be updated, and the password
stored in the Storage endpoint would get updated automatically.

Passwords are never stored in clear text.
A different sourcetype can be specified for each input, thus making
it possible to have separate mailboxes for each sourcetype.

The mailbox is also managed automatically, and emails are deleted once it has been indexed.


###Parameters

**mailserver** - This is a mandatory field and should be the hostname or
IP address for the mail server or client access server with support for retrieving emails via POP3 or IMAP

**is_secure** - This should be set to True / 1 if the server
 supports retreiving emails over SSL

**protocol** - This must be set to either POP3 or IMAP

**password** - Passwords must be set for every account,
or the input will get disabled.

**interval** - This should be configured to run as frequent as required
to retreive emails. This modular input retrieves up to 20 emails at each run.
This modular input supports multiple instances, so each input runs at seperate intervals.
A future update to this input might allow the limit to be configured as part of this input.


### Support
Support will be provided via Splunkbase :)

All support questions should include the version of Splunk, OS and mail server.

Please send feedback and feature requests on splunkbase.

Future update will support
1. a readonly flag - Prevent emails form getting deleted after indexing.
2. support for configuration of mail limits in inputs.conf
3. Support might be added for indexing text attachments.
4. Recursive option to read all folders inside Inbox, and not just emails within inbox.

**Note** : This has not been tested against an exhaustive list of mail servers, so I'll welcome the feedback.
