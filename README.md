
[![Donate](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/Seun/donate)

## Table of Contents

### OVERVIEW

- About the TA-mailclient
- Release notes
    - About this release
    - New features
    - To Do
    - Known issues
    - Third-party software attributions
    - Older Releases
- Support and resources

### INSTALLATION AND CONFIGURATION

- Hardware and software requirements
- Splunk Enterprise system requirements
- Download
- Installation steps
    - Deploy to single server instance
    - Deploy to distributed deployment
    - Deploy to Splunk Cloud
    - Configure TA-mailclient
        - Parameters
- Upgrade
- Copyright & License

### USER GUIDE

- Data types
- Troubleshooting
- Diagnostic & Debug Logs


---
### OVERVIEW

#### About the TA-mailclient

| Author | Oluwaseun Remi-Omosowon |
| --- | --- |
| App Version | 1.4.0 |
| Vendor Products | <ul><li>poplib</li><li>imaplib</li><li>SDK for Python 1.6.14</li></ul> |

The TA-mailclient add-on fetches emails for Splunk to index from mailboxes
using either POP3 or IMAP, with or without SSL.

The modular input also stores takes the password from inputs.conf in plain text,
and replaces it with a place holder, while storing it encrypted within Splunk.
This is built using the Splunk SDK for Python, should work on any Splunk
installation with Python available including SHC.
Passwords should also get replicated between search heard peer members.

This only fetches emails form the 'inbox' folder.
A future upgrade might include support for additional mailbox directories.

Be sure to set the interval to run this as frequently as required.

It supports all 'text/\*' content types and several well known scripts (.bat, .js, .sh) detailed below:

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
Images, videos and executables are not indexed.

##### Scripts and binaries

Includes:
- Splunk SDK for Python (1.6.14)
- Six python 2/3 compatibility (1.15.0)
- mail_lib - supports the calculation of vincenty distances which is used by default
    - constants.py - A number of constants / defaults used throughout the mail_lib module.
    - mail_common.py - Shared functions used to parse emails and attachments
    - exceptions raised by functions used in the mail_lib module.

#### Release notes

##### About this release

Version 1.4.1 of the TA-mailclient is compatible with:

| Splunk Enterprise versions | 8.x, 7.x |
| --- | --- |
| CIM | Not Applicable |
| Platforms | Platform independent |
| Lookup file changes | No lookups included in this app |

This version removes support for unencrypted connections to mailboxes to allow the app pass Splunk Certification. It supports IMAP on Splunk v7.x and 8.x, while POP3 is only supported on v8.x.

The administrator is responsible for setting the sourcetype to whatever is desired,
as well as extracting CIM fields for the sourcetype.
This app already includes several extractions for different parts of the message that can be reused.

This app will not work on a universal forwarder,
as it requires Python which comes with an HF or a full Splunk install.

**Note:** Travis CI includes tests for both secure and insecure versions of POP3 / IMAP. 

##### New features

TA-mailclient includes the following new features:

- Added support for Python 3
- Added six 1.15.0
- Upgraded Splunk SDK to 1.6.14

##### To Do

- Add attachment file hash to Splunk
- Add support for doc / ppt / pptx

##### Known issues

- This version does not support retrieving mails using POP3 on Splunk v7.x. It works when using IMAP.

This is currently tested against the latest version of Splunk Enterprise.
Issues can be reported and tracked on Github at this time.


##### Third-party software attributions

This uses the inbuilt poplib and imaplib that comes with Python by default.

Contributions on github are welcome and will be incorporated into the main release.
Current contributors are listed in AUTHORS.md.


##### Older Releases
* v1.4.0
    * Included support for Splunk v8.0
* v1.3.5
    * Fixed bug introduced  in v1.3.0
* v1.3.0
    * Made it more modular to supporting more file types in zips and in emails
    * Added support for zips and files within zips
    * Fixed unicode conversion of emails following contributions from Francois Lacombe on GitHub
        - Also added static mail preamble for line break. Event breaking configuration may not be
          required since the modular input writes individual events separately, but it's always a good idea.
    *  Additional logging from pop3 / imap 
    *  Removed interval from inputs.conf.spec
    *  Upgraded Splunk SDK to 1.6.2
    *  Added additional test cases on Travis CI to test that functionality work
    *  modularized storage/password functions to make them reusable and simpler
    *  Also fixed exception handling when dealing with storage/password
    *  Fixed type casting for boolean parameters (is\_secure, include\_headers) and port validation
    *  Rewrote sections of mail\_common
    *  Merged functions from poputils / imaputils into main code and added additional logs from connection

* v0.5.1
    * encoding corrections
    * deduplicate Date and MessageId from indexed headers
    * correction of MessageID extraction
    * changed the separator to a predefined one instead of Date and MessageID
    * activated and changed label for unsupported attachment

* v0.5.0
    * Fixed UTF-8 encoding of mails before indexing. (Supporting Gmail and others)

* v0.4.9
    * Changed encoding to support reading gmail.

* v0.4.8
    * removed error introduced in v0.4.7

* v0.4.7
    * Removed password field validation to allow users have complex or easy passwords however long
    * Handled all mail exceptions

* v0.4.6
    * Fixed bug.
    * Fixed header inclusion

* v0.4.5
    * Fixed bug. Removed line which caused v0.4.4 to fail
    * Fixed header inclusion

* v0.4.4
    * Updated app to ignore case of file attachment extension

* v0.4.3
    * Made extensions case insensitive
    * Added support for indexing _.docx_ extensions
    * Generalised ```Mail.save_password()``` to allow reuse of code when writing other modular inputs.
    * Optimized python import statements
    * Fixed deleting of mails in poplib which was broken in 0.4

* v0.4.2
    * Added support for indexing mail headers

* v0.4.1
    * Fixed bug with 0.4.0
    * Made updates to fix unneeded else statement which introduced bug in 0.4.0.

* v0.4
    * Added support for decoding unicode characters in other languages or and removing the unicode identifier in the header.
    * Improved support for indexing some file types even if the content-type is not set correctly. (as with Microsoft sending some files as binaries instead of text)
    * Added fundamental code to support indexing of attachment as a configurable option in future release by the user.
    * Added multiple field extractions for the email header and file attachments.
    * Introduced a bug which was corrected in 0.4.1 **Faulty version**

**Note:** _filename_ and _filecontent_ are multi-valve fields.

* v0.3
    * Adds support for mailbox cleanup options

* v0.2
    * Adds support for base64 encoded emails.


#### Support and resources

**Questions and answers**

Access questions and answers specific to the TA-mailclient at (https://answers.splunk.com/).

**Support**

This Splunk support add-on is community / developer supported.

Questions asked on Splunk answers will be answered either by the community of users or by the developer when available.
All support questions should include the version of Splunk and OS.

You can also contact the developer directly via [Splunkbase](https://splunkbase.splunk.com/app/3200/).
Feedback and feature requests can also be sent via Splunkbase.

Issues can also be submitted at the [TA-mailclient repo via on Github](https://github.com/seunomosowon/TA-mailclient/issues)

Future release will support
1. Support for configuration of mail limits in inputs.conf
2. Recursive option to read all folders inside Inbox, and not just emails within inbox.
3. Support indexing mails from additional folders in a mailbox

**Note** : This has not been tested against an exhaustive list of mail servers, so I'll welcome the feedback.

Also, feel free to send me a list of well known servers that you 're using this with without problems.

**Donations**

I have received a few requests on how to make donations, and have now added this section.
You can contact me for one-time paypal donations to my email or us Liberapay and stop it after one payment. 

[![Donate on Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/Seun/donate)

Rate the add-on on [Splunkbase](https://splunkbase.splunk.com/app/3200/) if you use it and are happy with it, 
and share your feedback. Thanks!


## INSTALLATION AND CONFIGURATION
### Hardware and software requirements

#### Hardware requirements

TA-mailclient supports the following server platforms in the versions supported by Splunk Enterprise:

- Linux
- Windows

The app was developed to be platform agnostic, but tests are mostly run on Linix.

Please contact the developer with issues running this on Windows. See the Splunk documentation for hardware
requirements for running a heavy forwarder.

#### Software requirements

To function properly, TA-mailclient has no external requirements but needs to be installed on a full Splunk
install which provides python and the required libraries (poplib and imaplib).

#### Splunk Enterprise system requirements

Because this add-on runs on Splunk Enterprise, all of the [Splunk Enterprise system requirements](http://docs.splunk.com/Documentation/Splunk/latest/Installation/Systemrequirements) apply.

#### Download

Download the TA-mailclient at one of the following locaitons:
- [Splunkbase](https://splunkbase.splunk.com/app/3200/#/details)
- [Github](https://github.com/seunomosowon/TA-mailclient)

#### Installation steps

##### Deploy to single server instance

To install and configure this app on your supported standalone platform, do one of the following:

- Install on a standalone Splunk Enterprise install via the GUI. [See Link](https://docs.splunk.com/Documentation/AddOns/released/Overview/Singleserverinstall)
- Extract the technology add-on to ```$SPLUNK_HOME/etc/apps/``` and restart Splunk

##### Deploy to distributed deployment

**Install to search head** - (Standalone or Search head cluster)

- Deploy the props.conf and transforms.conf from TA-mailclient to the search head. 
If using search head cluster, deploy the props.conf and transforms.conf via a search head deployer.


**Install to indexers**

- No App needs to be installed on indexers

**Install to forwarders**

- Follow the steps to install the TA-mailclient on a heavy forwarder.
More instructions available at the following [URL](https://docs.splunk.com/Documentation/AddOns/released/Overview/Distributedinstall#Heavy_forwarders)

- Configure an email input by going to the setup page or configuring inputs.conf.

##### Deploy to Splunk Cloud

For Splunk cloud installations, install TA-mailclient on a heavy forwarder that has been configured to forward
events to your Splunk Cloud instance. 
The sourcetype is set by the administrator of the heavy forwarder when configuring the inputs.

You can work with Splunk Support on installing the Support add-on on Splunk Cloud for parsing the mails collected.


#### Configure TA-mailclient

This app adds a mail:// modular input and supports a variety of parameters in inputs.conf.

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

The input can be edited if the password needs to be updated, and the password stored in a password
storage endpoint would get updated automatically. Passwords are never stored in clear text.

A different sourcetype can be specified for each input, thus making it possible to have different sourcetypes
for every mailbox. Mailbox cleanup is also managed automatically, and emails are deleted once it has been
indexed.

##### Parameters

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
A future release to this input might allow the limit to be configured as a parameter to the modular input.

This modular input supports multiple instances, and each input runs at separate intervals.

**include_headers** -  This determines if email headers should be included.


### Copyright & License

A copy of the Creative Commons Legal code has been added to the add-on detailing its license.


## USER GUIDE

### Data types

Data is indexed using a sourcetype specified by the administrator when configuring the inputs.
If nothing is specified, events will get indexed with a sourcetype of `mail`. 

### Troubleshooting

Once an email is indexed, it will not be re-indexed except the checkpoint directory is emptied.
This can be achieved by running the following command:
```
splunk clean inputdata mail
```

#### Diagnostic & Debug Logs

Logs can be found by searching Splunk internal logs

```index=_internal sourcetype=splunkd (component=ModularInputs OR component=ExecProcessor) mail.py```


Additional logging can be enabled by turning on debug logging for ExecProcessor and ModInputs.
set the logging level of the ExecProcessor to Debug

/opt/splunk/bin/splunk set log-level ExecProcessor -level DEBUG
/opt/splunk/bin/splunk set log-level ModInputs -level DEBUG

You can find additional ways to enable debug logging on
[here](http://docs.splunk.com/Documentation/Splunk/latest/Troubleshooting/Enabledebuglogging).
