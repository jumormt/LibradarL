from collections import defaultdict
import hashlib
import operator


def _get_invoked_apis(class_, api_set):
    ret = [ ]
    for method in class_.methods():
        for invoked_method in method.get_invoked_methods():
            if invoked_method in api_set:
                ret.append(invoked_method)
    return ret


def _calc_hash(lst):
    ret = hashlib.sha1()
    for s in sorted(lst):
        if type(s) is str:
            s = s.encode('utf8')
        ret.update(s)
    return ret.digest()


class PackageTree:
    def __init__(self, dex, api_set):
        # create an empty tree
        self.root = _TreeNode('')
        self.root.name = ''  # otherwise root.name will be 'L'

        # create tree nodes
        for class_ in dex.classes:
            name = class_.name()
            assert name.startswith('L')
            apis = _get_invoked_apis(class_, api_set)
            if len(apis) == 0: continue
            leaf = _TreeNode(name, _calc_hash(apis), len(apis))
            self.root.add_leaf(leaf)

        # calculate hash and weight
        self.nodes = { node.hash : node for node in self.root.finish() }


    ##  calculate match rate of potential libraries
    #   @param  exact_libs    exactly matched libraries
    def detect_libs(self, exact_libs, match_rate_threshold):
        for hash_, pkg in exact_libs:
            node = self.nodes[hash_]
            node.match_libs[pkg] = node.weight
        self.root.match_potential_libs()
        return self.root.get_all_libs(match_rate_threshold)


##  each tree node represents a package or a class
class _TreeNode:
    def __init__(self, name, hash_ = None, weight = None):
        self.name = 'L' + name[1:]  ## the package name (or full class name)
        self.hash = hash_           ## sha256 of children's hash (for package) or of invoked APIs' name (for class)
        self.weight = weight        ## number of API calls in this package

        self.parent = None
        if hash_ is None:  # not leaf (package)
            self.children = { }
        else:  # leaf (class)
            self.children = None

        self.match_libs = { }


    ##  insert a leaf to the tree; create missing nodes on the path to that leaf and set their name
    def add_leaf(self, node):
        assert node.name.startswith(self.name)
        assert node.name != self.name  # class name must be unique

        suffix = node.name[ len(self.name) + 1 : ]
        next_name = suffix.split('/', 1)[0]

        if '/' in suffix:  # inner package exist
            if next_name not in self.children:
                self.children[next_name] = _TreeNode(self.name + '/' + next_name)
            self.children[next_name].add_leaf(node)
            self.children[next_name].parent = self

        else:  # self is last layer
            self.children[next_name] = node


    ##  calculate the hash of every node
    def finish(self):
        if self.children is None: return [ self ]

        children_nodes = [ ]
        for c in self.children.values():
            children_nodes += c.finish()

        self.hash = _calc_hash([ c.hash for c in self.children.values() ])
        self.weight = sum( c.weight for c in self.children.values() )
        return [ self ] + children_nodes


    ##  search partially matched libraries in this node and its children
    def match_potential_libs(self):
        if len(self.match_libs) > 0 or self.children is None: return

        self.match_libs = defaultdict(int)
        for c in self.children.values():
            c.match_potential_libs()
            child_match = defaultdict(int)
            for child_pkg, weight in c.match_libs.items():
                pkg = child_pkg.rsplit('/', 1)[0]
                child_match[pkg] = max(child_match[pkg], weight)
            for pkg, weight in child_match.items():
                self.match_libs[pkg] += weight

        #if self.name.startswith('Ldebug'):
        #    print(self.hash.hex(), self.name, self.weight, self.match_libs)


    ##  get all matched libraries
    def get_all_libs(self, match_rate_threshold):
        if self.children is None: return { }    # assume libs are always packages instead of classes

        ret = { }

        if len(self.match_libs) > 0:
            pkg, weight = max(self.match_libs.items(), key = operator.itemgetter(1))
            pkgs = [ p for p, w in self.match_libs.items() if w == weight ]
            if self.name in pkgs:
                pkg = self.name
            elif len(pkgs) > weight:
                return ret  # small feature size and too many potential package names, not a lib
            if weight >= self.weight * match_rate_threshold:
                ret[self.name] = pkg
                #print(self.name, pkg, weight, self.weight, self.hash.hex())
            if weight == self.weight:
                return ret

        if self.children is None: return ret

        # add children's result to `ret` iff it's not a subpackage of self's matching lib
        lib = ret[self.name] if self.name in ret else None
        for c in self.children.values():
            if c.children is None: continue # ignore classes, only record packages
            for cpkg, clib in c.get_all_libs(match_rate_threshold).items():
                #if lib is None or not clib.startswith(lib):
                #    ret[cpkg] = clib
                ret[cpkg] = clib
        return ret
