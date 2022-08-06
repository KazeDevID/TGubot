import pathlib


work_dir = pathlib.Path(__file__).parent.absolute()

for path in work_dir.rglob("*.py[co]"):
    print(f"Removed '{path}'")
    path.unlink()

for dir in work_dir.rglob("__pycache__"):
    print(f"Removed '{dir}'")
    dir.rmdir()

print("\nAll Clean")
