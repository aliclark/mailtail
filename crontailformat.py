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

import sys
import re
import datetime
import time

bad_dom = re.compile(r'([a-zA-Z]{3})(, )([1-9])( )([a-zA-Z]{3})(.*)')

# 'Sun, 17 Feb 2013 17:42:28 +0000 (UTC)'
def tomillistamp(ids):
    ds = ids

    # strptime only accepts 2 digit day-of-month values, so if we have
    # a single digit value, zero pad it to 2 digits first.
    res = bad_dom.match(ids)
    if res:
        ds = res.group(1) + res.group(2) + '0' + res.group(3) + res.group(4) + res.group(5) + res.group(6)

    secshift = ((int(ds[26] + ds[27:29]) * 60) + int(ds[26] + ds[29:31])) * 60
    dt = datetime.datetime.strptime(ds[:25], '%a, %d %b %Y %H:%M:%S')
    return str(int(round(time.mktime(dt.timetuple())) - secshift) * 1000)

def doformat(folder, date, frm, subject):
    return ('.'.join(folder.split('.')[-2:]) + '\t' + tomillistamp(date) +
            '\t' + frm + '\t' + subject + '\n')

def main():
    try:
        line = sys.stdin.readline()
        m = re.compile('([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\n')

        while line:
            r = m.match(line)

            if r:
                line = doformat(r.group(1), r.group(2), r.group(3), r.group(4))

            print(line, end='')
            sys.stdout.flush()
            line = sys.stdin.readline()

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
