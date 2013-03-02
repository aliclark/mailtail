#!/usr/bin/python

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

"""

config = None

def error(x):
    print(x, file=sys.stderr)

def log(x):
    print(datetime.datetime.now().strftime("%H:%M:%S")+'.'+str(round(time.time()%1, 3))[2:] + ": " + x, file=sys.stderr)

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

def filter_exists(updates, rv=None):
    if rv == None:
        rv = []
    if updates:
        for x in updates:
            if (len(x) >= 2) and (x[1] == 'EXISTS'):
                rv.append(x[0])
    return rv

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

def start_listening_bg(f, headers):
    idling = False
    headersstr = 'BODY[HEADER.FIELDS (' + ' '.join(map(lambda x: x.upper(), headers)) + ')]'
    fetchtype = [headersstr]

    try:
        conn = imap_connection_new()

        log(f + ': conn.select_folder()')
        log(f + ': ' + str(conn.select_folder(f)))

        # reconnect in 29 mins time
        timeout_at = time.time() + (60 * 29)
        log(f + ': conn.idle()')
        idling = True
        ci = conn.idle()
        log(f + ': ' + str(ci))

        while True:
            tofetch = []
            # check for messages no longer than 29 mins at a time
            log(f + ': conn.idle_check(' + str(timeout_at) + ' - ' + str(time.time()) + ')')
            ic = conn.idle_check(timeout_at - time.time())
            log(f + ': ' + str(ic))
            filter_exists(ic, tofetch)

            # we might not need to do anything if eg. the update was just an expunge
            if tofetch or (time.time() >= timeout_at):
                log(f + ': conn.idle_done()')
                ix = conn.idle_done()
                idling = False
                log(f + ': ' + str(ix))
                filter_exists(ix[1], tofetch)

                if tofetch:
                    log(f + ': conn.fetch(' + str(tofetch) + ', ' + str(fetchtype) + ')')
                    cf = conn.fetch(tofetch, fetchtype)
                    log(f + ': ' + str(cf))

                    messages = map(lambda x: parse_headers(x[headersstr]), cf.values())
                    for m in messages:
                        line = '\t'.join([(m[h.upper()] if (h.upper() in m) else '') for h in headers])
                        log('print: ' + line)
                        print(f + (('\t' + line) if line else ''))
                        sys.stdout.flush()

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
        imap_connection_close(conn)

def start_listening(f, headers):
    p = Process(target=start_listening_bg, args=(f, headers))
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

    headersstr = 'BODY[HEADER.FIELDS (' + ' '.join(map(lambda x: x.upper(), headers)) + ')]'

    ls = []

    for f in mailboxes:
        ls.append(start_listening(f, headers))

    try:
        for l in ls:
            l.join()

    except KeyboardInterrupt:
        log('main thread shutting down')

    except Exception, e:
        error('exception: ' + str(e))

if __name__ == '__main__':
    main()
