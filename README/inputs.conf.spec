[mail://<name>]
* The name of the stanza should be an email address which would be used to connect to the server.

protocol = [POP3|IMAP]
* The protocol to be used to fetch emails from the server

mailserver = <value>
* This is the mailserver to fetch mails from

password = <value>
* The password for the account provided in the stanza name

is_secure = <bool>
* This determins if POPS/IMAPS should be used.

interval = [<number>|<cron schedule>]
* This inherits the interval parameter from the Splunk inputs.
* This should be set to occur frequently, as it fetches a maximum of 20 emails for each run.