import lx
from dex import Dex

import libdetect
import memdb

import sys
from zipfile import ZipFile


apk_list_file = sys.argv[1]
if len(sys.argv) > 2:
    threshold = int(sys.argv[2])
else:
    threshold = 0


def _extract_dex(apk_path):
    zf = ZipFile(apk_path)
    files = zf.namelist()
    if 'classes.dex' not in files: return [ ]
    path = lx.temp_file_dir()
    ret = [ zf.extract('classes.dex', path) ]
    i = 2
    while ('classes%d.dex' % i) in files:
        ret.append(zf.extract('classes%d.dex' % i, path))
        i += 1
    return ret


class PkgInfo:
    def __init__(self, pkg_cnt):
        self.count = sum(pkg_cnt.values())
        self.names = [ kv[0] for kv in sorted(pkg_cnt.items(), key = lambda kv: kv[1], reverse = True) ]


if __name__ == '__main__':
    for line in open(sys.argv[1]):
        apk_path = line.strip()
        if not apk_path: continue
        print('analyzing [%s]...' % apk_path)
        try:
            for dex_path in _extract_dex(apk_path):
                libdetect.add_dex_to_database(Dex(dex_path), db = memdb)
        except:
            print('cannot extract,pass!!')
        #lx.clear_temp_file()

    f = open('result.txt', 'w')

    pkgs = { hash_ : PkgInfo(info) for hash_, info in memdb._db_pkgs.items() if memdb._weight[hash_] >= threshold }
    for hash_, info in sorted(pkgs.items(), key = lambda kv: kv[1].count, reverse = True):
        s = '%s %d %s' % (hash_.hex(), info.count, ','.join(info.names))
        f.write(s + '\n')
        print(s)
