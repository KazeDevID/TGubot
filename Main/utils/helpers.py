# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError

import random
from typing import List


def arrange_buttons(array: list, no=3) -> List[list]:
    n = int(no)
    return [array[i * n : (i + 1) * n] for i in range((len(array) + n - 1) // n)]


def random_hash(length=8) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))
