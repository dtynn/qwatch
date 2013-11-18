#coding=utf-8
import pyinotify
from pyinotify import WatchManager, Notifier, ProcessEvent, ExcludeFilter, ThreadedNotifier, AsyncNotifier
from optparse import OptionParser
import logging
import json
from qiniu import rs as qRs, conf as qConf, io as qIo


logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)1.1s %(asctime)1.19s %(module)s:%(lineno)d] %(message)s')


class WatcherError(Exception):
    def __init__(self, message=None):
        Exception.__init__(self, "Watcher Error: %s" % (message,))


class processHandler(ProcessEvent):
    def my_init(self, **kargs):
        accessKey = kargs.get('ak')
        secretKey = kargs.get('sk')
        bucket = kargs.get('bucket')
        rootPath = kargs.get('root')
        if accessKey and secretKey and bucket and rootPath:
            qConf.ACCESS_KEY = accessKey
            qConf.SECRET_KEY = secretKey
            policy = qRs.PutPolicy(bucket)
            self.policy = policy
            return
        else:
            raise WatcherError('not enough parameters')

    def process_IN_CLOSE_WRITE(self, event):
        token = self.policy.token()
        key = ''
        qIo.put_file(token, key, event.pathname, None)
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
    basePath, confPath = optParser()
    if not basePath:
        raise WatcherError('need the base path')
    if not confPath:
        raise WatcherError('need a config file')

    with open(confPath, 'r') as conf:
        confContent = conf.read()

    if not confContent:
        raise WatcherError('Empty conf file')

    try:
        conf = json.loads(confContent)
        ak = conf.get('ak')
        sk = conf.get('sk')
        bucket = conf.get('bucket')
    except Exception as e:
        logging.error(e)
        raise WatcherError('not a valid json string')

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    excl_list = ['^.*/m3u8$', ]
    excl = ExcludeFilter(excl_list)
    wadd = wm.add_watch(basePath, mask, rec=True, exclude_filter=excl)
    notifier = Notifier(wm, processHandler(ak=ak, sk=sk, bucket=bucket))
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