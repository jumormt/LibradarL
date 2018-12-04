import lx

from .pkgtree import PackageTree
from . import filterlibs

from . import db
from . import thresholds


def detect_dex_libaries(dex, db = db, thresholds = thresholds):
    tree = PackageTree(dex, db.api_set)
    libs = db.match_libs(tree.nodes.keys())
    return tree.detect_libs(libs, thresholds.LibMatchRate)


def add_dex_to_database(dex, db = db, thresholds = thresholds):
    db.add_pkgs(_get_pkgs(dex, db, thresholds))

def remove_dex_from_database(dex, db = db, thresholds = thresholds):
    db.remove_pkgs(_get_pkgs(dex, db, thresholds))

def _get_pkgs(dex, db = db, thresholds = thresholds):
    tree = PackageTree(dex, db.api_set)
    pkgs = [ ]
    for node in tree.nodes.values():
        if node.weight < thresholds.MinApiWeight: continue
        if len(node.name) <= 2: continue  # 'L' + single letter
        if node.name in thresholds.PkgNameBlackList: continue
        pkgs.append(node)
    return pkgs


def update_library_database(db = db, thresholds = thresholds):
    filterlibs.main(db, thresholds)
