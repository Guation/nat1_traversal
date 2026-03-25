#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import os, shutil, tempfile, zipfile, sys, pathlib

def remove_pyd(dir: str):
    for i in os.scandir(dir):
        if i.is_file():
            if i.name.endswith(".pyd"):
                os.unlink(i.path)
        elif i.is_dir():
            remove_pyd(i.path)

def main():
    tmpdir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(sys.argv[1], 'r') as z:
            z.extractall(tmpdir)
        shutil.rmtree(pathlib.Path(tmpdir).joinpath("bin"))
        remove_pyd(tmpdir)
        os.unlink(sys.argv[1])
        with zipfile.ZipFile(sys.argv[1], 'w', zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmpdir):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, tmpdir)
                    z.write(full_path, rel_path)
    finally:
        shutil.rmtree(tmpdir)

if __name__ == "__main__":
    main()
