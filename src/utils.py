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
