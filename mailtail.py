#!/usr/bin/python

# Copyright (c) 2013, Ali Clark <ali@clark.gb.net>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from __future__ import print_function

import datetime
import time
import sys
import imapclient
from multiprocessing import Process
from configobj import ConfigObj

# Get a continuous stream of tab-separated email headers per line from mailboxes

# $ mailtail.py mailtail.conf
# $fold5\tSun, 17 Feb 2013 14:50:38 +0000\tBob Smith <bob.smith@example.net>\tA subject
# $fold3\tSun, 17 Feb 2013 14:59:25 +0000\tJohn Doe <john.doe@example.net>\tHi there
# ...

# mailtail.conf should look like:
example_conf = """

server = mail.example.net
username = user.name@example.net
password = s3cRetP4ss
mailboxes = INBOX, # trailing comma is important!
headers = date, from, subject
use_peek = True # default is True

"""

config = None

def error(x):
    print(x, file=sys.stderr)

def log(x):
    print(datetime.datetime.now().strftime("%H:%M:%S")+'.'+str(round(time.time()%1, 3))[2:].ljust(3, '0') + ": " + x, file=sys.stderr)

def imap_connection_new():
    conn = imapclient.IMAPClient(config['server'], use_uid=False, ssl=True)
    conn.login(config['username'], config['password'])
    return conn

def imap_connection_close(conn):
    if conn:
        try:
            conn.logout()
        except:
            pass

def expunge_update(f, ex, (tops, topu)):
    if ex <= tops:
        tops -= 1
    if ex > topu:
        log(f + ': eek, expunged an unknown mail')
    else:
        topu -= 1
    return (tops, topu)

def exists_update(f, ex, (tops, topu)):
    if ex < topu:
        log(f +': eek, mails unaccounted for')
    topu = ex
    if topu < tops:
        log(f + ': eek, fixing up tops')
        tops = topu
    return (tops, topu)

def run_updates(f, updates, (tops, topu)):
    if updates:
        log(f + ': before ' + str((tops, topu)))
        for x in updates:
            if len(x) >= 2:
                if x[1] == 'EXISTS':
                    (tops, topu) = exists_update(f, int(x[0]), (tops, topu))
                elif x[1] == 'EXPUNGE':
                    (tops, topu) = expunge_update(f, int(x[0]), (tops, topu))
        log(f + ': after ' + str((tops, topu)))
    return (tops, topu)

def parse_headers(s):
    h = {}
    curheader = None
    for line in s.splitlines():
        if (len(line) > 0) and (line[0] in (' ', '\t')):
            if not curheader:
                log('invalid header start')
                continue
            h[curheader] += ' ' + line.lstrip()
        else:
            p = line.find(': ')
            if p != -1:
                curheader = line[:p].upper()
                h[curheader] = line[p+2:]
    return h

def start_listening_bg(f, headers, use_peek):
    conn = None
    idling = False
    headersstr = 'BODY'+('.PEEK' if use_peek else '')+'[HEADER.FIELDS (' + ' '.join(map(lambda x: x.upper(), headers)) + ')]'
    headersstrkey = 'BODY[HEADER.FIELDS (' + ' '.join(map(lambda x: x.upper(), headers)) + ')]'
    fetchtype = [headersstr]

    try:
        conn = imap_connection_new()

        log(f + ': conn.select_folder(readonly='+str(use_peek)+')')
        csel = conn.select_folder(f, readonly=use_peek)
        log(f + ': ' + str(csel))

        tops = int(csel['EXISTS'])
        topu = tops

        # reconnect in 29 mins time
        timeout_at = time.time() + (60 * 29)
        log(f + ': conn.idle()')
        idling = True
        ci = conn.idle()
        log(f + ': ' + str(ci))

        while True:
            # check for messages no longer than 29 mins at a time
            log(f + ': conn.idle_check(' + str(timeout_at) + ' - ' + str(time.time()) + ')')
            ic = conn.idle_check(timeout_at - time.time())
            log(f + ': ' + str(ic))
            (tops, topu) = run_updates(f, ic, (tops, topu))

            # we might not need to do anything if eg. the update was just an expunge
            if (topu > tops) or (time.time() >= timeout_at):
                log(f + ': conn.idle_done()')
                ix = conn.idle_done()
                idling = False
                log(f + ': ' + str(ix))
                (tops, topu) = run_updates(f, ix[1], (tops, topu))

                if topu > tops:
                    tofetch = range(tops + 1, topu + 1)
                    log(f + ': conn.fetch(' + str(tofetch) + ', ' + str(fetchtype) + ')')
                    cf = conn.fetch(tofetch, fetchtype)
                    log(f + ': ' + str(cf))

                    messages = map(lambda x: parse_headers(x[headersstrkey]), [cf[m] for m in tofetch])
                    for m in messages:
                        line = '\t'.join([(m[h.upper()] if (h.upper() in m) else '') for h in headers])
                        log('print: ' + line)
                        print(f + (('\t' + line) if line else ''))
                        sys.stdout.flush()

                    tops = topu

                # connect again with timeout in 29 mins time
                timeout_at = time.time() + (60 * 29)
                log(f + ': conn.idle()')
                idling = True
                ci = conn.idle()
                log(f + ': ' + str(ci))

    except KeyboardInterrupt:
        log(f + ': listener shutting down')

    except Exception, e:
        log(f + ': idle exception: ' + str(e))

    finally:
        if idling:
            conn.idle_done()
        if conn:
            imap_connection_close(conn)

def start_listening(f, headers, use_peek):
    p = Process(target=start_listening_bg, args=(f, headers, use_peek))
    p.start()
    return p

def main():
    global config

    if len(sys.argv) <= 1:
        print('Please supply configuration file path as first argument', file=sys.stderr)
        sys.exit(1)

    config = ConfigObj(sys.argv[1])

    headers = config['headers']
    mailboxes = config['mailboxes']
    if 'use_peek' in config:
        use_peek = config['use_peek'] != 'False'
    else:
        use_peek = True

    # Test for idle
    conn = imap_connection_new()
    hasidle = conn.has_capability('IDLE')
    imap_connection_close(conn)

    if hasidle:
        ls = []

        for f in mailboxes:
            ls.append(start_listening(f, headers, use_peek))

        try:
            for l in ls:
                l.join()

        except KeyboardInterrupt:
            log('main thread shutting down')

        except Exception, e:
            error('exception: ' + str(e))

    else:
        # If the server does not advertise the IDLE capability, the
        # client MUST NOT use the IDLE command and must poll for
        # mailbox updates.
        # FIXME: implement polling using a single connection
        log(f + ': IDLE is not supported and polling not implemented, quitting')

if __name__ == '__main__':
    main()
