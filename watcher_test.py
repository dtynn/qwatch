#coding=utf-8
import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier,ProcessEvent, ExcludeFilter
from optparse import OptionParser


class processHandler(ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        print 'WRITE', event.pathname
        return

    def process_IN_MODIFY(self, event):
        print 'MODIFY', event.pathname
        return


def optParser():
    optp = OptionParser()
    #settings
    optp.add_option('-d', '--dir', help='directory',
                    dest='dir', default=None)

    opts, args = optp.parse_args()
    return opts.dir


def main():
    target_dir = optParser()

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MODIFY
    excl_list = ['^.*/m3u8$', ]
    excl = ExcludeFilter(excl_list)
    wadd = wm.add_watch('/home/videodemo/opentest/test_szy', mask, rec=True, exclude_filter=excl)
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
