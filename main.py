import sys
from util.robot import (Foreground, Background)


def main(argv):
    (Foreground if 'foreground' in argv else Background)().demo()


if __name__ == '__main__':
    main(sys.argv)
