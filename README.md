
mailtail
========

Get a continuous stream of tab-separated email headers from mailboxes

dependencies
============

The imapclient Python library is needed, this can be installed with:

```sh
sudo apt-get install python-pip
sudo easy_install imapclient
```

run
===

Edit the config file and supply it as the first argument to the script:

```sh
./mailtail.py mailtail.conf
```

The output can be converted into "base" format, which is compatible
with that accepted by the scripts in
https://github.com/aliclark/irctail

```sh
./mailtail.py mailtail.conf | ./mailtail-to-base.py
```

notes
=====

A better long term solution to this problem would be to patch getmail so it can
listen and download mail continuously using IDLE connections. A separate script
could then watch the local mailbox for any new emails.

This would first requre a patch for getmail to be able to download headers
only, however.

If you have been able to make those patches, please let me know so I can update
this readme :)
