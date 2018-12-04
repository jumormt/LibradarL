import lx


api_set = set( l.split(',', 1)[0] for l in lx.open_res_file(__file__, 'strict_api.csv') )

def match_libs(hash_list):
    sql = 'select hash, pkg_name from libraries where hash in ({ARGS})'
    return lx.query_multi('library', sql, list(hash_list))

#from collections import defaultdict
#
#_libs = defaultdict(list)
#for hash_, pkg in lx.query('library', 'select hash, pkg_name from libraries'):
#    _libs[hash_].append(pkg)
#
#def match_libs(hash_list):
#    ret = [ ]
#    for hash_ in hash_list:
#        for pkg in _libs[hash_]:
#            ret.append( (hash_, pkg) )
#    return ret

def add_pkgs(pkgs):
    sql = 'insert into packages (hash, pkg_name, weight, count) values (%s,%s,%s,1)' + \
            'on duplicate key update count = count + 1'
    lx.commit_multi('library', sql, [ (pkg.hash, pkg.name, pkg.weight) for pkg in pkgs ])

def remove_pkgs(pkgs):
    sql = 'update packages set count = count - 1 where hash=%s and pkg_name=%s and weight=%s'
    lx.commit_multi('library', sql, [ (pkg.hash, pkg.name, pkg.weight) for pkg in pkgs ])

def get_all_pkgs(threshold):
    sql = 'select hash, pkg_name, weight from packages where count >= %s'
    return lx.query('library', sql, threshold)

def add_libs(libs):
    sql = 'insert ignore into libraries (hash, pkg_name) values (%s,%s)'
    lx.commit_multi('library', sql, libs)
