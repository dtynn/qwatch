#coding=utf-8
import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier,ProcessEvent, ExcludeFilter
from optparse import OptionParser


class processHandler(ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        print event.pathname
        return


def optParser():
    optp = OptionParser()
    #settings
    optp.add_option('-d', '--dir', help='directory',
                    dest='dir', default=None)

    opts, args = optp.parse_args()
    return opts.dir


def main():
    targetDir = optParser()

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    excl_list = ['^.*/m3u8$', ]
    excl = ExcludeFilter(excl_list)
    wadd = wm.add_watch(targetDir, mask, rec=True, exclude_filter=excl)
    notifier = Notifier(wm, processHandler())
    while True:
        try:
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
        except KeyboardInterrupt:
            notifier.stop()
            break
    return


if __name__ == '__main__':
    main()