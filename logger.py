from datetime import datetime
import sys

from public import logFile

def printLog(s):
    t = datetime.now().strftime("[%Y-%m-%d %H:%M:%S::%f]")
    print('{0} {1}\n'.format(t, s), end='', file=sys.stderr, flush=True)
    print('{0} {1}\n'.format(t, s), end='', file=logFile, flush=True)
