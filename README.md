
mailtail
========

Get a continuous stream of tab-separated email headers from mailboxes

behaviour
=========

Note that currently all messages seen via this script will be marked as read.
In future I would like to make the default only be to peek at the message, with
an option to mark as read.

notes
=====

A better long term solution to this problem would be to patch getmail so it can
listen and download mail continuously using IDLE connections. A separate script
could then watch the local mailbox for any new emails.

This would first requre a patch for getmail to be able to download headers
only, however.

If you have been able to make those patches, please let me know so I can update
this readme :)

bugs
====

I've noticed some messages can be missed occasionally. From the logging I think
this is caused by a bug in either imapclient or the IMAP server I'm using.
Either way, be weary that you may still need to check email via some other
method.

