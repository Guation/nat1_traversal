#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "Guation"

import os, shutil, tempfile, zipfile, sys, pathlib, zipapp

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
        appfile = sys.argv[1]
        with open(appfile, 'rb') as f:
            assert f.read(2) == b"#!"
            shebang = f.readline().strip()
        with zipfile.ZipFile(appfile, 'r') as z:
            z.extractall(tmpdir)
        shutil.rmtree(pathlib.Path(tmpdir).joinpath("site-packages/bin"))
        remove_pyd(pathlib.Path(tmpdir).joinpath("site-packages"))
        os.unlink(appfile)
        zipapp.create_archive(tmpdir, appfile, interpreter=shebang, compressed=True)
    finally:
        shutil.rmtree(tmpdir)

if __name__ == "__main__":
    main()
