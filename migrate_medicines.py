import sqlite3
import mysql.connector

# SQLITE
sqlite_db = sqlite3.connect("database.db")
sqlite_cursor = sqlite_db.cursor()

# MYSQL
mysql_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Medical@123",
    database="medical_store"
)

mysql_cursor = mysql_db.cursor()

# GET SQLITE DATA
sqlite_cursor.execute("""
SELECT id,name,category,price,stock,expiry_date,image
FROM medicines
""")

rows = sqlite_cursor.fetchall()

count = 0

for row in rows:

    row = list(row)

    # Fix empty expiry date
    if row[5] == "":
        row[5] = None

    try:

        mysql_cursor.execute("""
            INSERT INTO medicines
            (
                id,
                name,
                category,
                price,
                stock,
                expiry_date,
                image
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, tuple(row))

        count += 1

    except Exception as e:
        print("Skipped:", e)
mysql_db.commit()

print(count, "medicines migrated")
