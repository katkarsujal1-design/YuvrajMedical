import sqlite3

db = sqlite3.connect("database.db")

cursor = db.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

tables = cursor.fetchall()

print("TABLES:")
print(tables)

print("\nMEDICINES:")

cursor.execute("SELECT * FROM medicines LIMIT 5")

rows = cursor.fetchall()

for row in rows:
    print(row)
