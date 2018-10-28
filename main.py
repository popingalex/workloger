from util.robot import (foreground, background)
def main(argv):
    foreground() if 'foreground' in argv else background()


if __name__ == '__main__':
    main(sys.argv)
