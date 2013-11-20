#coding=utf-8
import pyinotify
from pyinotify import WatchManager, Notifier, ProcessEvent, ExcludeFilter
import logging
import json
from qiniu import rs as qRs, conf as qConf, io as qIo
from optparse import OptionParser
from multiprocessing import Process,Pool


logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)1.1s %(asctime)1.19s %(module)s:%(lineno)d] %(message)s')


class WatcherError(Exception):
    def __init__(self, message=None):
        Exception.__init__(self, "Watcher Error: %s" % (message,))


def livePlaylist(content, prefix=None, listSize=3, allowCache=False):
    if not content:
        return ''
    contentList = filter(lambda x: bool(x), content.split('\n'))
    cacheTagCt = 0
    cacheTag = '#EXT-X-ALLOW-CACHE:YES' \
        if (allowCache is True) \
        else '#EXT-X-ALLOW-CACHE:NO'
    hasSegSec = False
    inSegSec = False
    segSecStart = -1
    segSecEnd = -1

    for n, c in enumerate(contentList):
        if c.startswith('#EXT-X-ALLOW-CACHE'):  # cache tag
            cacheTagCt += 1
            contentList[n] = cacheTag
        elif inSegSec is False and c.startswith('#EXTINF'):
            hasSegSec = True
            segSecStart = n
            inSegSec = True
        elif inSegSec is True and c.startswith('#') and c.startswith('#EXTINF') is not True:
            segSecEnd = n
            inSegSec = False
        else:
            pass

    if hasSegSec is True:
        headSec = contentList[:segSecStart]
        start = - listSize * 2
        segSec = contentList[segSecStart:][start:] if inSegSec else contentList[segSecStart:segSecEnd][start:]
        if prefix:
            for ln, line in enumerate(segSec):
                if line and line.startswith('#') is not True:
                    segSec[ln] = '%s%s' % (prefix, line)
        tailSec = [] if inSegSec else contentList[segSecEnd:]
        #return '%s\n%s\n%s' % ('\n'.join(headSec), '\n'.join(segSec), '\n'.join(tailSec))
        return '%s\n%s' % ('\n'.join(headSec), '\n'.join(segSec))
    else:
        return '\n'.join(contentList)


def listOutput(fPath, content):
    with file(fPath, 'w') as f:
        f.write(content)
    return


def uploader(token, key, filePath, putExtra):
    logging.info('Put: %s => %s' % (filePath, key))
    ret, err = qIo.put_file(token, key, filePath, putExtra)
    if err:
        res = 'fail'
    else:
        res = 'success'
    logging.info('%s: %s => %s' % (res, filePath, key))
    return


def liver(listPath, listDir, domain):
    liveListName = listPath.rsplit('/', 1)[-1]
    livePath = '%s/%s' % (listDir, liveListName)
    logging.info('Make playlist: %s => %s' % (listPath, livePath))
    with open(listPath, 'r') as f:
        content = f.read()
    liveContent = livePlaylist(content, domain)
    listOutput(livePath, liveContent)
    logging.info('Make playlist done:%s => %s' % (listPath, livePath))
    return


class processHandler(ProcessEvent):
    def my_init(self, **kargs):
        accessKey = kargs.get('ak')
        secretKey = kargs.get('sk')
        bucket = kargs.get('bucket')
        rootPath = kargs.get('root')
        domain = kargs.get('domain')
        listDir = kargs.get('listDir')
        if accessKey and secretKey and bucket and rootPath and domain and listDir:
            accessKey = str(accessKey)
            secretKey = str(secretKey)
            self.bucket = str(bucket)
            if not domain.endswith('/'):
                self.domain = '%s/' % (str(domain),)
            else:
                self.domain = str(domain)
            self.root = str(rootPath)
            self.listDir = str(listDir)
            qConf.ACCESS_KEY = accessKey
            qConf.SECRET_KEY = secretKey
            policy = qRs.PutPolicy(self.bucket)
            self.policy = policy
            return
        else:
            raise WatcherError('not enough parameters')

    def process_IN_CLOSE_WRITE(self, event):
        pathName = event.pathname
        if event.name.startswith('.') or event.name.endswith('~') or event.name == '4913':
            return
        elif event.name.endswith('.m3u8'):
            #make live list
            p = Process(target=liver, args=(pathName, self.listDir, self.domain))
            p.start()
            p.join()
            #pool = Pool(processes=1)
            #pool.apply_async(liver, (pathName, self.listDir, self.domain))
            #pool.close()
            #pool.join()
            return
        elif event.name.endswith('.ts'):
            key = pathName.split(self.root)[-1]
            self.policy.scope = '%s:%s' % (self.bucket, key)
            token = self.policy.token()
            #pool = Pool(processes=1)
            #pool.apply_async(uploader, (token, key,  pathName, None))
            #pool.close()
            #pool.join()
            p = Process(target=uploader, args=(token, key, pathName, None))
            p.start()
            p.join()
            #qIo.put_file(token, key, event.pathname, None)
            return
        else:
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

    if not basePath.endswith('/'):
        basePath = '%s/' % (basePath, )
        pass

    try:
        conf = json.loads(confContent)
        ak = conf.get('accesskey')
        sk = conf.get('secretkey')
        bucket = conf.get('bucket')
        domain = conf.get('domain')
        listDir = conf.get('listdir')
    except Exception as e:
        logging.error(e)
        raise WatcherError('invalid json string')

    wm = WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE
    excl_list = ['^.*/livelist', ]
    excl = ExcludeFilter(excl_list)
    wadd = wm.add_watch(basePath, mask, rec=True, exclude_filter=excl)
    notifier = Notifier(wm, processHandler(ak=ak, sk=sk, bucket=bucket, root=basePath, domain=domain, listDir=listDir))
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
