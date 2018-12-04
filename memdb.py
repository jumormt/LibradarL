from collections import defaultdict

from libdetect.db import api_set

# hash(bytes) -> package_name(str) -> count(int)
_db_pkgs = defaultdict(lambda: defaultdict(int))
# hash(bytes) -> package_name(str) -> count(int)
_db_libs = defaultdict(lambda: defaultdict(int))
# hash(bytes) -> weight(int)
_weight = { }

def match_libs(hash_list):
    ret = [ ]
    for hash_ in hash_list:
        for pkg in _db_libs[hash_].keys():
            ret.append( (hash_, pkg) )
    return ret

def add_pkgs(pkgs):
    for pkg in pkgs:
        _db_pkgs[pkg.hash][pkg.name] += 1
        _weight[pkg.hash] = pkg.weight

def remove_pkgs(pkgs):
    for pkg in pkgs:
        _db_pkgs[pkg.hash][pkg.name] -= 1

def get_all_pkgs(threshold):
    ret = [ ]
    for hash_, pkg_cnt in _db_pkgs.items():
        w = _weight[hash_]
        for pkg, cnt in pkg_cnt.items():
            if cnt >= threshold:
                ret.append( (hash_, pkg, w) )
    return ret

def add_libs(libs):
    for hash_, pkg in libs:
        _db_libs[hash_][pkg] += 1
