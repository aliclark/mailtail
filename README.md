
mailtail
========

Get a continuous stream of tab-separated email headers from mailboxes

behaviour
=========

Note that currently all messages seen via this script will be marked as read.
In future I would like to make the default only be to peek at the message, with
an option to mark as read.

bugs
====

I've noticed some messages can be missed occasionally. From the logging I think
this is caused by a bug in either imapclient or the IMAP server I'm using.
Either way, be weary that you may still need to check email via some other
method.

