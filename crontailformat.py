#!/usr/bin/python

from __future__ import print_function

import sys
import re
import datetime
import time

# 'Sun, 17 Feb 2013 17:42:28 +0000 (UTC)'
def tomillistamp(ds):
    secshift = ((int(ds[26] + ds[27:29]) * 60) + int(ds[26] + ds[29:31])) * 60
    dt = datetime.datetime.strptime(ds[:25], '%a, %d %b %Y %H:%M:%S')
    return str(int(round(time.mktime(dt.timetuple())) - secshift) * 1000)

def doformat(folder, date, frm, subject):
    return ('.'.join(folder.split('.')[-2:]) + '\t' + tomillistamp(date) +
            '\t' + frm + '\t' + subject + '\n')

def main():
    line = sys.stdin.readline()
    m = re.compile('([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\n')

    while line:
        r = m.match(line)

        if r:
            line = doformat(r.group(1), r.group(2), r.group(3), r.group(4))

        print(line, end='')
        sys.stdout.flush()
        line = sys.stdin.readline()

if __name__ == '__main__':
    main()
