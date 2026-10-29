from db_utils import get_connection

conn = get_connection()

cursor = conn.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='view'
ORDER BY name;
""")

views = cursor.fetchall()

print("=" * 50)
print("SQL Views")
print("=" * 50)

for view in views:
    print(view["name"])

conn.close()