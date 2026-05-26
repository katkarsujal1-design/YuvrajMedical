import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

medicines = [

# Pain Relief
("Paracetamol 500 mg Tablet","Pain Relief",10,100,"2026-12-01","default.jpg"),
("Paracetamol Syrup 125 mg/5ml","Pain Relief",20,80,"2026-12-01","default.jpg"),
("Paracetamol Injection 150 mg/ml","Pain Relief",30,50,"2026-12-01","default.jpg"),

("Aspirin 75 mg Tablet","Pain Relief",10,100,"2026-11-01","default.jpg"),
("Ibuprofen 200 mg Tablet","Pain Relief",15,100,"2026-10-10","default.jpg"),
("Ibuprofen Syrup 100 mg/5ml","Pain Relief",20,80,"2026-10-10","default.jpg"),

("Diclofenac 50 mg Tablet","Pain Relief",15,90,"2026-09-01","default.jpg"),
("Diclofenac Gel 20 gm","Pain Relief",25,60,"2026-09-01","default.jpg"),

# Anti Allergy
("Cetirizine 5 mg Tablet","Allergy",10,120,"2026-11-01","default.jpg"),
("Levocetirizine 5 mg Tablet","Allergy",15,100,"2026-11-01","default.jpg"),
("Chlorpheniramine 4 mg Tablet","Allergy",10,90,"2026-10-01","default.jpg"),

# Antibiotics
("Amoxicillin 500 mg Capsule","Antibiotic",50,80,"2026-09-01","default.jpg"),
("Amoxicillin Syrup 125 mg/5ml","Antibiotic",40,70,"2026-09-01","default.jpg"),
("Azithromycin 500 mg Tablet","Antibiotic",80,60,"2026-09-01","default.jpg"),
("Ciprofloxacin 500 mg Tablet","Antibiotic",60,75,"2026-09-01","default.jpg"),
("Doxycycline 100 mg Capsule","Antibiotic",55,70,"2026-09-01","default.jpg"),

# Anti Fungal
("Fluconazole 150 mg Tablet","Antifungal",70,60,"2026-08-01","default.jpg"),
("Clotrimazole Cream 1%","Antifungal",45,50,"2026-08-01","default.jpg"),

# Diabetes
("Metformin 500 mg Tablet","Diabetes",30,100,"2027-01-01","default.jpg"),
("Glimepiride 2 mg Tablet","Diabetes",40,80,"2027-01-01","default.jpg"),

# Cardio
("Amlodipine 5 mg Tablet","Cardio",20,90,"2027-01-01","default.jpg"),
("Telmisartan 40 mg Tablet","Cardio",50,70,"2027-01-01","default.jpg"),
("Atorvastatin 10 mg Tablet","Cardio",60,80,"2027-01-01","default.jpg"),

# GI Medicines
("Omeprazole 20 mg Capsule","Gastric",25,100,"2026-12-01","default.jpg"),
("Ranitidine 150 mg Tablet","Gastric",20,80,"2026-12-01","default.jpg"),

# ORS
("ORS Powder Sachet","General",20,150,"2027-01-01","default.jpg"),

# Skin
("Betamethasone Cream 0.05%","Dermatology",40,60,"2026-12-01","default.jpg"),
("Calamine Lotion","Dermatology",35,70,"2026-12-01","default.jpg"),

# Eye
("Ciprofloxacin Eye Drops","Eye",50,50,"2026-12-01","default.jpg"),
("Timolol Eye Drops","Eye",60,40,"2026-12-01","default.jpg"),

# Misc
("Hydrogen Peroxide Solution","General",30,60,"2026-12-01","default.jpg"),
("Ethyl Alcohol 70%","General",50,80,"2026-12-01","default.jpg"),

]

c.executemany("""
INSERT INTO medicines (name, category, price, stock, expiry_date, image)
VALUES (?, ?, ?, ?, ?, ?)
""", medicines)

conn.commit()
conn.close()

print("✅ All medicines inserted successfully!")