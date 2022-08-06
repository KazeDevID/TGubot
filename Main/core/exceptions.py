# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError


class NoDatabaseConnected(Exception):
    def __init__(self, message):
        super().__init__(message)


class Package404(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class AlreadyInstalled(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidPackageToUpdate(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class EnvVariableTypeError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidInputTime(Exception):
    def __init__(self, message):
        super().__init__(message)
