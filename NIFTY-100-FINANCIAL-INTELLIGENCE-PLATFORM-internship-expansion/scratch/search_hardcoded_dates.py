import os
import glob
import re

base = "."
py_files = glob.glob(f"{base}/src/**/*.py", recursive=True)

print("Searching for hardcoded 2024 / 2023 / date bounds in python files:\n")
for f in py_files:
    rel = os.path.relpath(f, base)
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        lines = fp.readlines()
    matches = []
    for i, line in enumerate(lines):
        if re.search(r'\b2024\b', line):
            matches.append((i+1, line.strip()))
    if matches:
        print(f"File: {rel} ({len(matches)} occurrences)")
        for line_no, text in matches[:10]:
            print(f"  Line {line_no:4d}: {text[:100]}")
        if len(matches) > 10:
            print(f"  ... and {len(matches)-10} more")
        print()
