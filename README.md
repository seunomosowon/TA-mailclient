# TA-mailclient

This technology adapter add-on fetches emails for Splunk to index from mailboxes
using either POP3 or IMAP, with or without SSL.

The modular input also stores takes the password from inputs.conf in plain text,
and replaces it with a place holder, while storing it encrypted within Splunk.
This is built using the Splunk SDK for Python, should work on any Splunk
installation with Python available including SHC.
Passwords should also get replicated between search heard peer members.

This only fetches emails form the 'inbox' folder for IMAP.

It supports all 'text/*' content types and several well known scripts (.bat, .js, .sh) detailed below:

By default, it fetches up to 25 new emails at every run.
Be sure to set the interval to run this as frequently as required.
```
'application/xml'
'application/xhtml'
'application/x-sh'
'application/x-csh',
'application/javascript'
'application/bat'
'application/x-bat'
'application/x-msdos-program'
'application/textedit'
```
Images and videos and executables are not indexed.

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
mailbox_cleanup = delete

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

**protocol** - This must be set to either POP3 or IMAP

**is_secure** - This should be set to 1 if emails should be retrieved using the
protocol selected over SSL.

**password** - Passwords must be set for every account,
or the input will get disabled.

**mailbox_cleanup** = This indicates if every email should be deleted as it is read,
  or delayed until the next interval.
  Setting this to ```readonly``` prevents mails from being deleted.

  The default is ```readonly```. Supported options are:
```delayed|delete|readonly```

**interval** - This should be configured to run as frequent as required
to retreive emails. This modular input retrieves up to 20 emails at each run.
This modular input supports multiple instances, so each input runs at seperate intervals.
A future update to this input might allow the limit to be configured as part of this input.

**include_headers** -  This determines if email headers should be included.


### Support
Support will be provided via Splunkbase :)

All support questions should include the version of Splunk, OS and mail server.

Please send feedback and feature requests on splunkbase.

Future update will support
1. Support for configuration of mail limits in inputs.conf
2. Recursive option to read all folders inside Inbox, and not just emails within inbox.

**Note** : This has not been tested against an exhaustive list of mail servers, so I'll welcome the feedback.

Also, feel free to send me a list of well known servers that you 're using this with without problems.

Once an email is indexed, it will not be re-indexed except the checkpoint directory is emptied.
This can be achieved by running the following command:
```
splunk clean inputdata mail
```

#### Getting errors?

If you're getting errors with using this modular input,
set the logging level of the ExecProcessor to Debug

/opt/splunk/bin/splunk set log-level ExecProcessor -level DEBUG
/opt/splunk/bin/splunk set log-level ModInputs -level DEBUG

You can find some diagnostic logs by searching with 
```index=_internal sourcetype=splunkd (component=ModularInputs OR component=ExecProcessor) mail.py```

