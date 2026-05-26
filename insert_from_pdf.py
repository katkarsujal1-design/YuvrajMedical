import sqlite3
import pdfplumber

conn = sqlite3.connect("database.db")
c = conn.cursor()

pdf_path = "essentialmedicineslist2013_2.pdf"

medicines = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()

        for table in tables:
            for row in table:
                if row and row[0]:
                    name = row[0].strip()

                    # Skip headers
                    if "medicine" in name.lower():
                        continue

                    medicines.append((
                        name,
                        "General",
                        10,
                        100,
                        "2026-12-01",
                        "default.jpg"
                    ))

c.executemany("""
INSERT INTO medicines (name, category, price, stock, expiry_date, image)
VALUES (?, ?, ?, ?, ?, ?)
""", medicines)

conn.commit()
conn.close()

print("✅ Medicines imported from PDF!")