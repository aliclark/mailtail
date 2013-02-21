#!/usr/bin/python

from __future__ import print_function

import datetime
import time
import sys
import imapclient
from multiprocessing import Process, Queue
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
        p = line.find(': ')
        if p != -1:
            curheader = line[:p].upper()
            h[curheader] = line[p+2:]
    return h

def start_listening_bg(f, headersstr, task_queue):
    idling = False
    fetchtype = [headersstr]

    try:
        conn = imap_connection_new()

        log(f + ': conn.select_folder()')
        log(f + ': ' + str(conn.select_folder(f)))

        # reconnect in 29 mins time
        timeout_at = time.time() + (60 * 29)
        log(f + ': conn.idle()')
        log(f + ': ' + str(conn.idle()))
        idling = True

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
                log(f + ': ' + str(ix))
                filter_exists(ix[1], tofetch)
                idling = False

                if tofetch:
                    log(f + ': conn.fetch(' + str(tofetch) + ', ' + str(fetchtype) + ')')
                    cf = conn.fetch(tofetch, fetchtype)
                    log(f + ': ' + str(cf))
                    task_queue.put(('fetched', f, cf))

                # connect again with timeout in 29 mins time
                timeout_at = time.time() + (60 * 29)
                log(f + ': conn.idle()')
                log(f + ': ' + str(conn.idle()))
                idling = True

    except KeyboardInterrupt:
        log(f + ': listener shutting down')
        pass

    except Exception, e:
        log(f + ': idle exception: ' + str(e))

    finally:
        if idling:
            conn.idle_done()
        imap_connection_close(conn)

def start_listening(f, headersstr, task_queue):
    p = Process(target=start_listening_bg, args=(f, headersstr, task_queue))
    p.start()
    return p

def main():
    global config
    config = ConfigObj(sys.argv[1])

    headers = config['headers']
    mailboxes = config['mailboxes']

    headersstr = 'BODY[HEADER.FIELDS (' + ' '.join(map(lambda x: x.upper(), headers)) + ')]'

    task_queue = Queue()

    ls = []

    for f in mailboxes:
        ls.append(start_listening(f, headersstr, task_queue))

    try:
        while True:
            obj = task_queue.get()
            log('got task: ' + str(obj))

            if (type(obj) == tuple) and (len(obj) > 0):
                t = obj[0]
            else:
                t = None

            if t == 'fetched':
                messages = map(lambda x: parse_headers(x[headersstr]), obj[2].values())
                for m in messages:
                    line = '\t'.join([(m[h.upper()] if (h.upper() in m) else '') for h in headers])
                    log('print: ' + line)
                    print(obj[1] + (('\t' + line) if line else ''))
                    sys.stdout.flush()

            elif t == 'error':
                error('error: ' + str(obj[1]))

            else:
                error('unknown object type: ' + str(obj))

    except KeyboardInterrupt:
        log('main thread shutting down')
        pass

    except Exception, e:
        error('exception: ' + str(e))

if __name__ == '__main__':
    main()
