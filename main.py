import sys
from util.robot import (foreground, Background)


def main(argv):
    foreground() if 'foreground' in argv else Background().demo()


if __name__ == '__main__':
    main(sys.argv)
