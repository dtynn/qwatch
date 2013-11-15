#coding=utf-8
import pyinotify
from pyinotify import WatchManager, Notifier, ProcessEvent, ExcludeFilter
from optparse import OptionParser
import logging


logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)1.1s %(asctime)1.19s %(module)s:%(lineno)d] %(message)s')


class processHandler(ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        print event.pathname
        return


def optParser():
    optp = OptionParser()
    #settings
    optp.add_option('-d', '--dir', help='directory',
                    dest='dir', default=None)
    optp.add_option('-c', '--conf', help='config file',
                    dest='conf', default=None)

    opts, args = optp.parse_args()
    return opts.dir, opts.conf


def main():
    basePath, confFile = optParser()
    if not basePath:
        logging.error('Need a path to watch')
        return
    if not confFile:
        logging.error('Need a config file')
        return

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    excl_list = ['^.*/m3u8$', ]
    excl = ExcludeFilter(excl_list)
    wadd = wm.add_watch(basePath, mask, rec=True, exclude_filter=excl)
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