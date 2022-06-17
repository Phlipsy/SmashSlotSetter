import os


def find_in_dict(dic, regex):
    routes = []

    def find_rec(route, d):
        for k in d:
            if regex.fullmatch(k):
                routes.append(route+[k])
            elif d[k]:
                find_rec(route+[k], d[k])

    find_rec([], dic)
    return routes


def find_file_in_dict(dic, char):
    routes = []

    def find_rec(route, d):
        for k in d:
            if not d[k] and char in k:
                routes.append(route+[k])
            elif d[k]:
                find_rec(route+[k], d[k])

    find_rec([], dic)
    return routes


def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def tabbed_join(lst, tabs):
    t = "\n"+"      "*tabs
    return "      "*tabs+t.join(["/".join(l) if type(l) == list else l for l in lst])


# https://stackoverflow.com/a/7205107
def merge_dicts(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a
