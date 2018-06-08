#!/usr/bin/env python3
# Copyright (C) 2010-2016,2018 XCG Consulting <http://odoo.consulting>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import os.path
import sys


def main():
    if len(sys.argv) != 4:
        print("usage: autotodo.py <folder> <exts> <tags>")
        sys.exit(1)

    folder = sys.argv[1]
    exts = sys.argv[2].split(',')
    tags = sys.argv[3].split(',')
    todolist = {tag: [] for tag in tags}

    for root, dirs, files in os.walk(folder):
        scan_folder((exts, tags, todolist), root, files)
    create_autotodo(folder, todolist)


def write_info(f, infos, folder):
    # Check sphinx version for lineno-start support

    import sphinx

    if sphinx.version_info < (1, 3):
        lineno_start = False
    else:
        lineno_start = True

    for i in infos:
        path = i[0]
        line = i[1]
        lines = (line - 3, line + 4)
        class_name = (
            ":class:`%s`" %
            os.path.basename(os.path.splitext(path)[0])
        )
        f.write(
            "%s\n"
            "%s\n\n"
            "Line %s\n"
            "\t.. literalinclude:: %s\n"
            "\t\t:language: python\n"
            "\t\t:lines: %s-%s\n"
            "\t\t:emphasize-lines: %s\n"
            %
            (
                class_name,
                "-" * len(class_name),
                line,
                path,
                lines[0], lines[1],
                line,
            )
        )
        if lineno_start:
            f.write("\t\t:lineno-start: %s\n" % lines[0])
        f.write("\n")


def create_autotodo(folder, todolist):
    with open('autotodo', 'w+') as f:
        for tag, info in list(todolist.items()):
            f.write("%s\n%s\n\n" % (tag, '=' * len(tag)))
            write_info(f, info, folder)


def scan_folder(data_tuple, dirname, names):
    (exts, tags, res) = data_tuple
    file_info = {}
    for name in names:
        (root, ext) = os.path.splitext(name)
        if ext in exts:
            file_info = scan_file(os.path.join(dirname, name), tags)
            for tag, info in list(file_info.items()):
                if info:
                    res[tag].extend(info)


def scan_file(filename, tags):
    res = {tag: [] for tag in tags}
    with open(filename, 'r') as f:
        for line_num, line in enumerate(f):
            for tag in tags:
                if tag in line:
                    res[tag].append((filename, line_num, line[:-1].strip()))
    return res


if __name__ == "__main__":
    main()
