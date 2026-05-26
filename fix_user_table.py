import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Add Aadhar column
try:
    c.execute("ALTER TABLE staff ADD COLUMN aadhar TEXT")
    print("✅ Aadhar column added")
except Exception as e:
    print("⚠ Aadhar exists or skipped:", e)

# Add PAN column
try:
    c.execute("ALTER TABLE staff ADD COLUMN pan TEXT")
    print("✅ PAN column added")
except Exception as e:
    print("⚠ PAN exists or skipped:", e)

conn.commit()
conn.close()

print("🎯 DONE")