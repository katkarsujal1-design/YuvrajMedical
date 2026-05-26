import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# -------------------------------
# USERS TABLE
# -------------------------------
c.execute("""
        CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    role TEXT NOT NULL,
    password TEXT,
    hashed_password TEXT
)
""")

# -------------------------------
# MEDICINES TABLE
# -------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    stock INTEGER,
    expiry_date TEXT,
    image TEXT
)
""")

# -------------------------------
# ORDERS TABLE
# -------------------------------
c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total REAL,
    date TEXT,
    status TEXT DEFAULT 'Pending',
    prescription TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# -------------------------------
# ORDER ITEMS TABLE
# -------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    medicine_id INTEGER,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(medicine_id) REFERENCES medicines(id)
)
""")

# -------------------------------
# FEEDBACK TABLE
# -------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    date TEXT
)
""")
#----------------------------------
#CART TABLE
#---------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    medicine_id INTEGER,
    quantity INTEGER,
    UNIQUE(user_id, medicine_id)
)
""")

#-------------------------------------------
#Staff database
#--------------------------------------------
c.execute("""
        CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    address TEXT,
    education TEXT,
    email TEXT UNIQUE,
    age INTEGER,
    gender TEXT,
    religion TEXT,
    aadhar TEXT,
    pan TEXT
)
""")

#---------------------------------------
#FEEDBACK TABLE
#--------------------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# -------------------------------
# SAFE MIGRATION (NO DATA LOSS)
# -------------------------------

# Add status column if old DB already exists
try:
    c.execute("ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'Pending'")
except:
    pass

conn.commit()
conn.close()

print("✅ Database Updated Safely (No Data Lost)")
