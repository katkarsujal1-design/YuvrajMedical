import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

rows = c.execute("SELECT * FROM medicines").fetchall()

print("Total medicines:", len(rows))

if len(rows) == 0:
    print("❌ No data found in medicines table!")
else:
    print("✅ Sample data:")
    for r in rows[:5]:
        print(r)

conn.close()