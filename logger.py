from datetime import datetime
import sys

def printLog(s):
    t = datetime.now().strftime("[%Y-%m-%d %H:%M:%S::%f]")
    print('{0} {1}'.format(t, s), file=sys.stderr, flush=True)
