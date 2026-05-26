import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

data = [
    ("Paracetamol", "/static/medicine/paracetamol.jpg"),
    ("Aspirin", "/static/medicine/aspirin.jpg"),
    ("Ibuprofen", "/static/medicine/ibuprofen.jpg"),
]

cur.executemany(
    "INSERT OR REPLACE INTO medicine_images VALUES (?, ?)",
    data
)

conn.commit()
conn.close()
print("Images inserted successfully")