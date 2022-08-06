# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


import pathlib


def get_all_files_in_path(path):
    path = pathlib.Path(path)
    return [i.absolute() for i in path.glob("**/*")]
