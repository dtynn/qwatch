#coding=utf-8
from optparse import OptionParser


def livePlaylist(content, prefix=None, listSize=3, allowCache=False):
    if not content:
        return ''
    contentList = content.split('\n')
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
        seqSec = contentList[segSecStart:][start:] if inSegSec else contentList[segSecStart:segSecEnd][start:]
        if prefix:
            for ln, line in enumerate(seqSec):
                if line.startswith('#') is not True:
                    seqSec[ln] = '%s%s' % (prefix, line)
        tailSec = [] if inSegSec else contentList[segSecEnd:]
        return '%s\n%s\n%s' % ('\n'.join(headSec), '\n'.join(seqSec), '\n'.join(tailSec))
    else:
        return '\n'.join(contentList)


def optParser():
    optp = OptionParser()
    #settings
    optp.add_option('-p', '--prefix', help='prefix',
                    dest='prefix', default=None)
    optp.add_option('-o', '--output', help='output file path',
                    dest='output', default=None)
    optp.add_option('-i', '--input', help='input file path',
                    dest='input', default=None)
    optp.add_option('-l', '--listsize', help='m3u8 list size',
                    dest='listsize', default=3)
    optp.add_option('-c', '--cache', help='allow cache',
                    dest='cache', default=None)

    opts, args = optp.parse_args()
    return opts.prefix, opts.input, opts.output, int(opts.listsize), bool(opts.cache)


def listOutput(fPath, content):
    with file(fPath, 'w') as f:
        f.write(content)
    return


def main():
    prefix, fInput, fOutput, listSize, allowCache = optParser()

    if not fInput:
        print 'need a file'
        return

    with file(fInput, 'r') as f:
        content = f.read()
        result = livePlaylist(content, prefix, listSize, allowCache)
        print result
        if fOutput:
            listOutput(fOutput, result)
        return


if __name__ == '__main__':
    main()