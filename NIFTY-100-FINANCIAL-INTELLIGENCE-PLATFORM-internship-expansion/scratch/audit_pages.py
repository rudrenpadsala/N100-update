import os
import glob
import re

pages_dir = "src/dashboard/pages"
files = glob.glob(f"{pages_dir}/*.py")

print("AUDIT OF DASHBOARD PAGES:\n")
for f in sorted(files):
    name = os.path.basename(f)
    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
        content = fp.read()
    
    # Check imports from db
    db_imports = re.findall(r'from utils\.db import ([\w\s,]+)', content)
    # Check sql queries
    sql_queries = re.findall(r'SELECT .*? FROM \w+', content, re.IGNORECASE)
    # Check max years or date logic
    year_mentions = re.findall(r'[\'"](?:202\d|Mar \d{4}|Sep \d{4})[\'"]', content)
    
    print(f"Page: {name:<22}")
    if db_imports:
        print(f"  DB imports: {', '.join([x.strip() for x in db_imports])}")
    if sql_queries:
        print(f"  Direct SQL queries: {sql_queries}")
    if year_mentions:
        print(f"  Explicit year strings: {set(year_mentions)}")
    print("-" * 50)
