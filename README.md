
mailtail
========

Get a continuous stream of tab-separated email headers from mailboxes

notes
=====

A better long term solution to this problem would be to patch getmail so it can
listen and download mail continuously using IDLE connections. A separate script
could then watch the local mailbox for any new emails.

This would first requre a patch for getmail to be able to download headers
only, however.

If you have been able to make those patches, please let me know so I can update
this readme :)

