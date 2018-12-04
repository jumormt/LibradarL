try:
    import pymysql
    import oss2
    import oss2.exceptions
except ModuleNotFoundError as e:
    pass

from datetime import datetime
from json import dumps
import os
import os.path
from pathlib import Path
import random
import shutil
import sys
import traceback


##  Debugging

_debug = True

def debug_mode():
    return _debug

def set_mode(mode):
    global _debug
    assert mode == 'debug' or mode == 'release'
    _debug = (mode != 'release')


##  SQL database

_conns = { }

def connect_db(db = 'main', user = 'dev', password = 'Oslab1435go'):
    if db not in _conns:
        _conns[db] = pymysql.connect(
            host = 'rm-2ze710p770jn5k96o.mysql.rds.aliyuncs.com',
            user = user,
            password = password,
            db = db,
            charset = 'utf8'
        )
    return _conns[db]

def reconnect_db():
    _conns.clear()

def query(db, sql, args = None, multi = False):
    cursor = connect_db(db).cursor()
    if args is None:
        cursor.execute(sql)
    else:
        cursor.execute(sql, args)
    ret = cursor.fetchall()
    if len(ret) == 0: return [ ] if multi else None
    if len(ret[0]) == 1:
        ret = [ row[0] for row in ret ]
    if len(ret) == 1 and not multi: return ret[0]
    return ret

def query_multi(db, sql, arg_list):
    assert '{ARGS}' in sql and '%s' not in sql
    sql = sql.format(ARGS = ','.join('%s' for a in arg_list))
    cursor = connect_db(db).cursor()
    cursor.execute(sql, arg_list)
    ret = cursor.fetchall()
    if len(ret) == 0: return ret
    if len(ret[0]) == 1:
        return [ row[0] for row in ret ]
    else:
        return ret

def commit(db, sql, args):
    db = connect_db(db)
    db.cursor().execute(sql, args)
    db.commit()

def commit_multi(db, sql, arg_list):
    db = connect_db(db)
    db.cursor().executemany(sql, arg_list)
    db.commit()


## Aliyun OSS

_bkts = { }

def oss(bucket = 'lxapk'):
    if bucket not in _bkts:
        auth = oss2.Auth('LTAI19YfqOSkHpRW', 'pmxBQkjnHYmnTmoExeG5w7Vdk4laMK')
        _bkts[bucket] = oss2.Bucket(auth, 'vpc100-oss-cn-beijing.aliyuncs.com', bucket)
    return _bkts[bucket]

def oss_upload(local, remote, bucket = 'lxapk'):
    if type(local) is bytes:
        oss(bucket).put_object(remote, local)
    else:
        oss(bucket).put_object_from_file(remote, local)

def oss_download(remote, local = None, bucket = 'lxapk'):
    if local is None:
        local, f = create_temp_file()
    try:
        oss(bucket).get_object_to_file(remote, local)
    except oss2.exceptions.NoSuchKey:
        return None
    return local

def oss_download_apk(pkg, md5, sha256):
    if type(md5) is bytes:
        md5 = md5.hex()
    if type(sha256) is bytes:
        sha256 = sha256.hex()
    key = pkg + '/' + md5 + '-' + sha256 + '.apk'
    return oss_download(key)

def oss_download_dex(pkg, md5):
    if type(md5) is bytes: md5 = md5.hex()
    key = pkg + '/' + md5 + '/dex.zip'
    return oss_download(key, bucket = 'lxzip')

def oss_get_size(key, bucket = 'lxapk'):
    return oss(bucket).get_object_meta(key).content_length


##  local resource file

def res_file_path(script_path, file_name):
    relative = os.path.dirname(script_path)
    absolute = os.path.abspath(relative)
    return os.path.join(absolute, file_name)

def open_res_file(script_path, file_name, mode = 'r'):
    return open(res_file_path(script_path, file_name), mode)


##  file system

def _prepare_path(path):
    Path(os.path.dirname(path)).mkdir(parents = True, exist_ok = True)

def mv(src, dst):
    _prepare_path(dst)
    shutil.move(src, dst)

def rm(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def create_file(path, data = None):
    _prepare_path(path)
    if type(data) is str:
        data = data.encode('utf8')
    f = open(path, 'wb')
    if data is None:
        return f
    else:
        f.write(data)

def ls(path):
    return sorted(os.listdir(path))

def file_exists(path):
    return os.path.isfile(path)

_global_temp_file_dir = '/tmp/lx/'
_temp_file_idx = 0

def _temp_file_dir():
    return _global_temp_file_dir + str(os.getpid()) + '/'

def temp_file_dir():
    path = _temp_file_dir()
    _prepare_path(path)
    return path

def create_temp_file():
    global _temp_file_idx
    path = _temp_file_dir() + str(_temp_file_idx)
    _temp_file_idx += 1
    f = create_file(path)
    return path, f

def clear_temp_file():
    rm(_temp_file_dir())

def open_file(path, mode = 'r'):
    try:
        return open(path, mode)
    except FileNotFoundError:
        return None

def read_lines(path):
    f = open_file(path)
    if f is None: return None
    return [ l[:-1] for l in f ]


##  log

_log_file = None
_echo = False

def enable_echo():
    global _echo
    _echo = True

def _log(msg, level):
    if isinstance(msg, Exception):
        msg = '\n' + traceback.format_exc()
    time = str(datetime.now()).split('.')[0]
    msg = '%s [%s] %s\n' % (time, level, msg)
    _write_log(msg)

def debug(msg):
    if not _debug: return
    _log(msg, 'debug')

def verbose(msg):
    if not _debug: return
    _log(msg, 'verbose')

def info(msg):
    _log(msg, 'info')

def warning(msg):
    _log(msg, 'warning')

def error(msg):
    _log(msg, 'error')
    if _debug: sys.exit(1)

def _write_log(msg):
    global _log_file

    if _debug:
        print(msg, end='')
        return

    if _echo:
        print(msg, end='')

    if _log_file is None:
        file_name = 'log/%d.txt' % os.getpid()
        _prepare_path(file_name)
        _log_file = open(file_name, 'a')

    _log_file.write(msg)
    _log_file.flush()


##  misc

def json(obj, pretty = False):
    if pretty:
        return dumps(obj, ensure_ascii = False, indent = 2, sort_keys = True)
    else:
        return dumps(obj, ensure_ascii = False, separators = (',', ':'))

def decision(probability):
    return random.random() <= probability

def exit(code = 0):
    sys.exit(code)
