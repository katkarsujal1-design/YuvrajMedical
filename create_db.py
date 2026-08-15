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
    return_status TEXT DEFAULT 'Not Requested',
    refund_status TEXT DEFAULT 'Not Applicable',
    delivery_status TEXT DEFAULT 'Pending',
    delivery_otp TEXT,
    delivery_notes TEXT,
    delivery_address TEXT,
    courier_name TEXT,
    courier_tracking_id TEXT,
    courier_tracking_url TEXT,
    delivery_updated_at TEXT,
    payment_method TEXT DEFAULT 'Cash On Delivery',
    payment_status TEXT DEFAULT 'Pending',
    payment_reference TEXT,
    payment_screenshot TEXT,
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
# PAYMENTS TABLE
# -------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    user_id INTEGER,
    method TEXT,
    amount REAL,
    transaction_id TEXT,
    screenshot TEXT,
    status TEXT DEFAULT 'Pending Verification',
    notes TEXT,
    created_at TEXT,
    verified_at TEXT,
    verified_by INTEGER,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
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
# REVIEWS & FEEDBACK TABLE
# -------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS reviews_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    review_type TEXT,
    medicine_id INTEGER,
    order_id INTEGER,
    rating INTEGER,
    title TEXT,
    message TEXT,
    issue_category TEXT,
    status TEXT DEFAULT 'Submitted',
    created_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(medicine_id) REFERENCES medicines(id),
    FOREIGN KEY(order_id) REFERENCES orders(id)
)
""")

# -------------------------------
# NOTIFICATIONS TABLE
# -------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    title TEXT,
    message TEXT,
    target_url TEXT,
    dedupe_key TEXT UNIQUE,
    is_read INTEGER DEFAULT 0,
    created_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# -------------------------------
# PRESCRIPTION REQUESTS TABLE
# -------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS prescription_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    family_member_id INTEGER,
    prescription_image TEXT NOT NULL,
    ocr_text TEXT,
    detected_medicines TEXT,
    approved_medicines TEXT,
    status TEXT DEFAULT 'Pending Review',
    staff_note TEXT,
    reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
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

for column_sql in [
    "ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'Cash On Delivery'",
    "ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'Pending'",
    "ALTER TABLE orders ADD COLUMN payment_reference TEXT",
    "ALTER TABLE orders ADD COLUMN payment_screenshot TEXT",
]:
    try:
        c.execute(column_sql)
    except:
        pass

conn.commit()
conn.close()

print("✅ Database Updated Safely (No Data Lost)")
