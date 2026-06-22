from flask import Flask, render_template, request, redirect, session, g, jsonify
#import pymysql
import hashlib
import re
import secrets
import requests
from rapidfuzz import fuzz
import pytesseract
from PIL import Image
import barcode
from barcode.writer import ImageWriter
from flask import flash
import pandas as pd
import mysql.connector
from mysql.connector import pooling
import os
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY","my-super-secret")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000


app.config["SESSION_PERMANENT"] = True
app.permanent_session_lifetime = timedelta(days=7)

#=================         ===========================
@app.teardown_appcontext
def close_db(error):

    db = g.pop("db", None)

    if db is not None:
        db.close()

# ================= DB CONNECTION =================
db_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME")
)


def get_db():

    if "db" not in g:

        g.db = db_pool.get_connection()

    return g.db


LOGIN_MAX_FAILED_ATTEMPTS = 5
LOGIN_LOCK_MINUTES = 15
OTP_EXPIRY_MINUTES = 10
OTP_RESEND_SECONDS = 10


def ensure_auth_security_schema():
    if app.config.get("AUTH_SECURITY_SCHEMA_READY"):
        return

    db = get_db()
    cursor = db.cursor()

    user_columns = [
        "ADD COLUMN email_verified TINYINT(1) DEFAULT 0",
        "ADD COLUMN two_factor_enabled TINYINT(1) DEFAULT 0",
        "ADD COLUMN failed_login_attempts INT DEFAULT 0",
        "ADD COLUMN locked_until DATETIME NULL",
    ]

    for column_sql in user_columns:
        try:
            cursor.execute(f"ALTER TABLE users {column_sql}")
        except mysql.connector.Error:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_otps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            email VARCHAR(255) NOT NULL,
            purpose VARCHAR(40) NOT NULL,
            otp_hash VARCHAR(255) NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            used_at DATETIME NULL,
            INDEX idx_auth_otps_email_purpose (email, purpose)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            email VARCHAR(255) NOT NULL,
            ip_address VARCHAR(80),
            user_agent TEXT,
            status VARCHAR(20) NOT NULL,
            reason VARCHAR(255),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_login_activity_user (user_id, created_at)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_devices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            device_hash VARCHAR(128) NOT NULL,
            user_agent TEXT,
            ip_address VARCHAR(80),
            trusted TINYINT(1) DEFAULT 0,
            is_active TINYINT(1) DEFAULT 1,
            first_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_user_device (user_id, device_hash),
            INDEX idx_user_devices_user (user_id, last_seen)
        )
    """)

    db.commit()
    cursor.close()
    app.config["AUTH_SECURITY_SCHEMA_READY"] = True


@app.before_request
def prepare_auth_security():
    ensure_auth_security_schema()


def client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or ""


def current_device_hash():
    raw_device = f"{request.headers.get('User-Agent', '')}|{client_ip()}"
    return hashlib.sha256(raw_device.encode("utf-8")).hexdigest()


def hash_otp(otp):
    return generate_password_hash(str(otp))


def create_otp(db, user_id, email, purpose):
    otp = f"{secrets.randbelow(1000000):06d}"
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO auth_otps (user_id, email, purpose, otp_hash, expires_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user_id,
        email,
        purpose,
        hash_otp(otp),
        datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    ))
    db.commit()
    cursor.close()
    return otp


def normalize_fast2sms_number(phone):
    digits = re.sub(r"\D", "", str(phone or ""))

    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    if len(digits) != 10:
        return None

    return digits


def send_phone_otp(phone, otp):
    sms_otp_mode = os.environ.get("SMS_OTP_MODE", "live").strip().lower()
    fast2sms_api_key = os.environ.get("FAST2SMS_API_KEY")
    fast2sms_url = os.environ.get("FAST2SMS_API_URL", "https://www.fast2sms.com/dev/bulkV2")
    fast2sms_number = normalize_fast2sms_number(phone)

    if sms_otp_mode != "live":
        print(f"Development registration OTP for {phone}: {otp}")
        return True, f"Development OTP: {otp}"

    if not fast2sms_number:
        print(f"SMS OTP not sent: Fast2SMS requires a valid 10 digit Indian mobile number. Got {phone}.")
        return False, "Use a valid 10 digit Indian mobile number."

    if fast2sms_api_key and fast2sms_api_key != "your_api_key_here":
        try:
            response = requests.post(
                fast2sms_url,
                headers={
                    "authorization": fast2sms_api_key,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cache-Control": "no-cache",
                },
                data={
                    "route": "otp",
                    "variables_values": str(otp),
                    "numbers": fast2sms_number,
                },
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            if result.get("return") is True:
                return True, None

            print("Fast2SMS OTP send failed:", result)
            return False, result.get("message") or "Fast2SMS rejected the OTP request."
        except (ValueError, requests.RequestException) as error:
            print("Fast2SMS OTP send failed:", error)
            return False, "Fast2SMS request failed. Check the API key, wallet balance, and network."

    print(f"Registration OTP for {phone}: {otp}")
    print("SMS OTP not sent: set FAST2SMS_API_KEY to enable Fast2SMS delivery.")
    return False, "FAST2SMS_API_KEY is missing or still set to the placeholder."


def verify_otp(db, email, purpose, otp):
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM auth_otps
        WHERE email=%s AND purpose=%s AND used_at IS NULL AND expires_at >= %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (email, purpose, datetime.now()))
    rows = cursor.fetchall()

    for row in rows:
        if check_password_hash(str(row["otp_hash"]), str(otp)):
            cursor.execute(
                "UPDATE auth_otps SET used_at=%s WHERE id=%s",
                (datetime.now(), row["id"])
            )
            db.commit()
            cursor.close()
            return True

    cursor.close()
    return False


def log_login_activity(db, user_id, email, status, reason):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO login_activity (user_id, email, ip_address, user_agent, status, reason)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        email,
        client_ip(),
        request.headers.get("User-Agent", ""),
        status,
        reason
    ))
    db.commit()
    cursor.close()


def record_device(db, user_id):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO user_devices (user_id, device_hash, user_agent, ip_address, last_seen)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            user_agent=VALUES(user_agent),
            ip_address=VALUES(ip_address),
            is_active=1,
            last_seen=VALUES(last_seen)
    """, (
        user_id,
        current_device_hash(),
        request.headers.get("User-Agent", ""),
        client_ip(),
        datetime.now()
    ))
    db.commit()
    cursor.close()


def login_redirect_for(user):
    if user["role"] == "owner":
        return redirect("/owner_dashboard")
    if user["role"] == "staff":
        return redirect("/staff")
    return redirect("/")


def complete_login(db, user):
    session.clear()
    session.permanent = True
    session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }

    cursor = db.cursor()
    cursor.execute("""
        UPDATE users
        SET failed_login_attempts=0, locked_until=NULL
        WHERE id=%s
    """, (user["id"],))
    db.commit()
    cursor.close()

    record_device(db, user["id"])
    log_login_activity(db, user["id"], user["email"], "success", "Login successful")
    return login_redirect_for(user)


def render_login(**context):
    db = get_db()
    activity = []
    devices = []

    if "user" in session:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT email, ip_address, status, reason, created_at
            FROM login_activity
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 8
        """, (session["user"]["id"],))
        activity = cursor.fetchall()

        cursor.execute("""
            SELECT id, user_agent, ip_address, trusted, is_active, last_seen
            FROM user_devices
            WHERE user_id=%s
            ORDER BY last_seen DESC
            LIMIT 8
        """, (session["user"]["id"],))
        devices = cursor.fetchall()
        cursor.close()

    return render_template("login.html", activity=activity, devices=devices, **context)

# ================= Prescription upload ===============
PRESCRIPTION_FOLDER = "static/prescriptions"

def read_prescription_text(image_path):
    try:
        import cv2
        import pytesseract
        from PIL import Image
        import numpy as np

        # Read image
        img = cv2.imread(image_path)

        if img is None:
            return ""
        # Resize image bigger for OCR
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Remove noise
        gray = cv2.medianBlur(gray, 3)

        # Improve contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=20)

        # Threshold image
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15
        )

        # Try multiple OCR modes
        configs = [
            "--oem 3 --psm 6",
            "--oem 3 --psm 11",
            "--oem 3 --psm 12"
        ]

        best_text = ""

        for config in configs:
            text = pytesseract.image_to_string(thresh, config=config)
            if len(text.strip()) > len(best_text.strip()):
                best_text = text

        return best_text.strip()

    except Exception as e:
        print("OCR Error:", e)
        return ""
def save_image(file):

    upload_folder = os.path.join("static", "images")

    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)

    filepath = os.path.join(upload_folder, filename)

    file.save(filepath)

    return "/" + filepath.replace("\\", "/")
#===================barcode image==========================
def generate_barcode_image(barcode_number):
    folder = "static/barcodes"
    os.makedirs(folder, exist_ok=True)

    filename = f"{folder}/{barcode_number}"

    code128 = barcode.get("code128", barcode_number, writer=ImageWriter())
    saved_path = code128.save(filename)

    return saved_path
#======================== Auto classification ==============================
def classify_medicine(name):

    name = name.lower()

    diabetes = ["metformin", "glimepiride", "insulin", "sitagliptin"]
    cardiac = ["amlodipine", "telmisartan", "atorvastatin", "losartan"]
    antibiotics = ["amoxicillin", "azithromycin", "ciprofloxacin", "cefixime"]
    vitamins = ["vitamin", "calcium", "zinc", "b12", "d3"]
    liver = ["liv", "silymarin", "ursodeoxycholic"]

    prescription_keywords = [
        "antibiotic", "azithromycin", "amoxicillin", "ciprofloxacin",
        "insulin", "metformin", "amlodipine", "telmisartan",
        "steroid", "prednisolone", "tramadol"
    ]

    department = "General"

    if any(x in name for x in diabetes):
        department = "Diabetes"
    elif any(x in name for x in cardiac):
        department = "Cardiac"
    elif any(x in name for x in antibiotics):
        department = "Antibiotics"
    elif any(x in name for x in vitamins):
        department = "Vitamins"
    elif any(x in name for x in liver):
        department = "Liver"

    prescription_required = any(x in name for x in prescription_keywords)

    return department, prescription_required


def normalize_category(category):
    category = "" if category is None else str(category).strip()
    if not category or category.lower() == "nan":
        return "General"
    return category


BASIC_MEDICINE_TYPES = [
    {"name": "Tablet", "aliases": ["Tablet"], "image": "images/categories/tablet.jpeg"},
    {"name": "Capsule", "aliases": ["Capsule"], "image": "images/categories/capsule.jpeg"},
    {"name": "Syrup", "aliases": ["Syrup"], "image": "images/categories/syrup.jpeg"},
    {"name": "Injection", "aliases": ["Injection"], "image": "images/categories/injection.jpeg"},
    {"name": "Drops", "aliases": ["Drops", "Eye Drops"], "image": "images/categories/drops.jpeg"},
    {"name": "Cream", "aliases": ["Cream"], "image": "images/categories/cream.jpeg"},
    {"name": "Gel", "aliases": ["Gel"], "image": "images/categories/gel.jpeg"},
    {"name": "Ointment", "aliases": ["Ointment"], "image": "images/categories/ointment.jpeg"},
]
# ================= HOME (SEARCH + FILTER) =================
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    # ROLE BASED REDIRECT
    if session["user"]["role"] == "owner":
        return redirect("/owner_dashboard")

    elif session["user"]["role"] == "staff":
        return redirect("/staff")

    db = get_db()

    search = request.args.get("search", "")
    sort = request.args.get("sort", "")
    category = request.args.get("category", "")

    query = "SELECT * FROM medicines WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE %s"
        params.append(f"%{search}%")

    if category:
        query += " AND category = %s"
        params.append(category)

    if sort == "low":
        query += " ORDER BY price ASC"
    elif sort == "high":
        query += " ORDER BY price DESC"

    cursor = db.cursor(dictionary=True)
    cursor.execute(query, params)
    medicines = cursor.fetchall()
    cursor.close()

    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicine_id, quantity
        FROM cart
        WHERE user_id=%s
    """, (user_id,))
    cart_rows = cursor.fetchall()
    cursor.close()
    
    cart = {str(r["medicine_id"]): r["quantity"] for r in cart_rows}
    cart_count = sum(cart.values())
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM disease_categories
        ORDER BY display_order
    """)    

    disease_cards = cursor.fetchall()
    cursor.close()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, COUNT(*) AS count
        FROM (
            SELECT COALESCE(NULLIF(TRIM(category), ''), 'General') AS name
            FROM medicines
        ) AS medicine_categories
        GROUP BY name
        ORDER BY name ASC
    """)
    category_counts = {
        row["name"]: row["count"]
        for row in cursor.fetchall()
    }
    medicine_types = []
    for medicine_type in BASIC_MEDICINE_TYPES:
        medicine_types.append({
            "name": medicine_type["name"],
            "image": medicine_type["image"],
            "count": sum(category_counts.get(alias, 0) for alias in medicine_type["aliases"])
        })
    cursor.close()

    dashboard_context = build_customer_dashboard_context(db, user_id)

    return render_template(
        "index.html",
        medicines=medicines,
        disease_cards=disease_cards,
        medicine_types=medicine_types,
        cart=cart,
        cart_count=cart_count,
        search=search,
        sort=sort,
        category=category,
        **dashboard_context
     )
# ========================== Department ====================
@app.route("/department/<disease_name>")
def department_page(disease_name):

    if "user" not in session:
        return redirect("/login")

    db = get_db()

    mapping = {
        "Heart": "Cardiac",
        "Diabetes": "Diabetes",
        "Respiratory": "Respiratory",
        "Skin Care": "Skin Care",
        "Liver": "Liver",
        "Gastric": "Gastric",
        "Pain Relief": "Pain Relief",
        "Cold & Cough": "Cold & Cough",
        "Vitamins": "Vitamins",
        "General": "General"
    }

    department = mapping.get(disease_name, "General")

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM medicines
        WHERE department=%s
        ORDER BY name ASC
    """, (department,))
    medicines = cursor.fetchall()
    cursor.close()

    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicine_id, quantity
        FROM cart
        WHERE user_id=%s
    """, (user_id,))
    cart_rows = cursor.fetchall()
    cursor.close()

    cart = {str(r["medicine_id"]): r["quantity"] for r in cart_rows}
    cart_count = sum(cart.values())

    return render_template(
        "department.html",
        dept_name=disease_name,
        medicines=medicines,
        cart=cart,
        cart_count=cart_count
    )
# =================== Search  ========================
@app.route("/medicine_suggestions")
def medicine_suggestions():

    if "user" not in session:
        return jsonify([])

    query = request.args.get("q", "").strip()[:100]

    if not query:
        return jsonify([])

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT name
        FROM medicines
        WHERE name IS NOT NULL
          AND name LIKE %s
        ORDER BY
            CASE WHEN name LIKE %s THEN 0 ELSE 1 END,
            name ASC
        LIMIT 8
    """, (f"%{query}%", f"{query}%"))
    medicines = cursor.fetchall()
    cursor.close()

    return jsonify([medicine["name"] for medicine in medicines])


@app.route("/search_medicine")
def search_medicine():

    if "user" not in session:
        return redirect("/login")

    db = get_db()

    search = request.args.get("search", "")

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM medicines
        WHERE name LIKE %s
        ORDER BY name ASC
    """, (f"%{search}%",))
    medicines = cursor.fetchall()
    cursor.close()

    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicine_id, quantity
        FROM cart
        WHERE user_id=%s
    """, (user_id,))
    cart_rows = cursor.fetchall()
    cursor.close()

    cart = {str(r["medicine_id"]): r["quantity"] for r in cart_rows}
    cart_count = sum(cart.values())

    return render_template(
        "department.html",
        dept_name=f"Search Results for '{search}'",
        medicines=medicines,
        cart=cart,
        cart_count=cart_count
    )
# ================= LOGIN =================
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
               "SELECT * FROM users WHERE email=%s",
               (email,)
        )

        user = cursor.fetchone()

        if user:
            locked_until = user.get("locked_until")

            if locked_until and locked_until > datetime.now():
                cursor.close()
                log_login_activity(db, user["id"], email, "locked", "Account is temporarily locked")
                return render_login(
                    error=f"Account locked. Try again after {locked_until.strftime('%d %b %Y, %I:%M %p')}."
                )

            pass_login = False

            # ================= HASHED PASSWORD =================
            if user["hashed_password"]:

                if check_password_hash(
                    str(user["hashed_password"]),
                    str(password)
                ):
                    pass_login = True

            # ================= OLD PASSWORD =================
            elif user.get("password") == password:

                pass_login = True

                # convert old password to hashed
                new_hash = generate_password_hash(password)

                cursor.execute(
                    "UPDATE users SET hashed_password=%s WHERE id=%s",
                    (new_hash, user["id"])
                )

                db.commit()

            # ================= LOGIN SUCCESS =================
            if pass_login:
                if user.get("two_factor_enabled"):
                    otp = create_otp(db, user["id"], user["email"], "login_2fa")
                    session.clear()
                    session["pending_2fa_user_id"] = user["id"]
                    session["pending_2fa_email"] = user["email"]
                    cursor.close()
                    log_login_activity(db, user["id"], email, "pending_2fa", "Password accepted, OTP required")
                    return render_login(
                        show_2fa=True,
                        message=f"2FA code generated for this login: {otp}"
                    )

                cursor.close()
                return complete_login(db, user)

            failed_attempts = int(user.get("failed_login_attempts") or 0) + 1
            locked_until = None
            reason = "Invalid password"

            if failed_attempts >= LOGIN_MAX_FAILED_ATTEMPTS:
                locked_until = datetime.now() + timedelta(minutes=LOGIN_LOCK_MINUTES)
                reason = f"Locked after {LOGIN_MAX_FAILED_ATTEMPTS} failed attempts"

            cursor.execute("""
                UPDATE users
                SET failed_login_attempts=%s, locked_until=%s
                WHERE id=%s
            """, (failed_attempts, locked_until, user["id"]))
            db.commit()
            cursor.close()
            log_login_activity(db, user["id"], email, "failed", reason)

            if locked_until:
                return render_login(
                    error=f"Too many failed attempts. Account locked until {locked_until.strftime('%d %b %Y, %I:%M %p')}."
                )
        else:
            cursor.close()
            log_login_activity(db, None, email, "failed", "Unknown email")

        return render_login(error="Invalid email or password.")

    return render_login()


@app.route("/two_factor", methods=["POST"])
def two_factor():
    if "pending_2fa_user_id" not in session:
        return redirect("/login")

    email = session["pending_2fa_email"]
    otp = request.form.get("otp", "")
    db = get_db()

    if not verify_otp(db, email, "login_2fa", otp):
        log_login_activity(db, session["pending_2fa_user_id"], email, "failed", "Invalid 2FA OTP")
        return render_login(show_2fa=True, error="Invalid or expired 2FA code.")

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s", (session["pending_2fa_user_id"],))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        session.clear()
        return render_login(error="Account not found.")

    return complete_login(db, user)


@app.route("/two_factor/setup", methods=["POST"])
def two_factor_setup():
    if "user" not in session:
        return redirect("/login")

    action = request.form.get("action")
    db = get_db()

    if action == "disable":
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET two_factor_enabled=0 WHERE id=%s",
            (session["user"]["id"],)
        )
        db.commit()
        cursor.close()
        return render_login(message="Two-factor authentication disabled.")

    otp = create_otp(db, session["user"]["id"], session["user"]["email"], "2fa_setup")
    return render_login(message=f"Enter this setup code to enable 2FA: {otp}", show_2fa_setup=True)


@app.route("/two_factor/enable", methods=["POST"])
def two_factor_enable():
    if "user" not in session:
        return redirect("/login")

    otp = request.form.get("otp", "")
    db = get_db()

    if not verify_otp(db, session["user"]["email"], "2fa_setup", otp):
        return render_login(error="Invalid or expired setup code.", show_2fa_setup=True)

    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET two_factor_enabled=1 WHERE id=%s",
        (session["user"]["id"],)
    )
    db.commit()
    cursor.close()
    return render_login(message="Two-factor authentication enabled.")


@app.route("/login_activity")
def login_activity():
    if "user" not in session:
        return redirect("/login")
    return render_login(show_activity=True)


@app.route("/devices")
def devices():
    if "user" not in session:
        return redirect("/login")
    return render_login(show_devices=True)


@app.route("/devices/<int:device_id>/remove", methods=["POST"])
def remove_device(device_id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE user_devices
        SET is_active=0
        WHERE id=%s AND user_id=%s
    """, (device_id, session["user"]["id"]))
    db.commit()
    cursor.close()
    return redirect("/devices")
# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        country_code = request.form.get("country_code", "+91").strip()
        phone_number = request.form.get("phone_number", request.form.get("phone", "")).strip()
        full_phone = f"{country_code}{phone_number}"
        form_data = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "country_code": country_code,
            "phone_number": phone_number,
            "phone": full_phone,
            "password": request.form.get("password", ""),
            "role": request.form.get("role", "customer"),
            "address": request.form.get("address", "").strip(),
            "age": request.form.get("age", "").strip(),
            "gender": request.form.get("gender", "").strip(),
            "religion": request.form.get("religion", "").strip(),
            "education": request.form.get("education", "").strip(),
            "aadhar": request.form.get("aadhar", "").strip(),
            "pan": request.form.get("pan", "").strip(),
        }
        action = request.form.get("action", "create_account")
        db = get_db()

        try:
            required_fields = ["name", "email", "phone", "password", "address"]
            if any(not form_data[field] for field in required_fields):
                return render_template(
                    "register.html",
                    error="Please fill all required fields.",
                    form=form_data
                )

            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT id FROM users WHERE email=%s OR phone=%s LIMIT 1",
                (form_data["email"], form_data["phone"])
            )
            existing_user = cursor.fetchone()
            cursor.close()

            if existing_user:
                return render_template(
                    "register.html",
                    error="An account with this email or phone already exists.",
                    form=form_data
                )

            if action == "send_otp":
                otp = create_otp(db, None, form_data["email"], "register_account")
                sms_sent, sms_message = send_phone_otp(form_data["phone"], otp)
                message = sms_message or "OTP sent to your phone number. Please enter it below."
                if not sms_sent:
                    message = f"OTP could not be sent. {sms_message}"
                return render_template(
                    "register.html",
                    message=message if sms_sent else None,
                    error=None if sms_sent else message,
                    otp_sent=True,
                    resend_seconds=OTP_RESEND_SECONDS,
                    form=form_data
                )

            otp = request.form.get("otp", "").strip()
            if not otp:
                return render_template(
                    "register.html",
                    error="Please send and enter the OTP before creating the account.",
                    form=form_data
                )

            if not verify_otp(db, form_data["email"], "register_account", otp):
                return render_template(
                    "register.html",
                    error="Invalid or expired OTP. Please send a new OTP.",
                    otp_sent=True,
                    form=form_data
                )

            hashed_password = generate_password_hash(form_data["password"])
            role = "staff" if form_data["role"] == "staff" else "customer"

            # -------- CUSTOMER --------
            if role == "customer":
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    INSERT INTO users (name, email, phone, address, role, hashed_password, email_verified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    form_data["name"],
                    form_data["email"],
                    form_data["phone"],
                    form_data["address"],
                    "customer",
                    hashed_password,
                    1
                ))

            # -------- STAFF --------
            elif role == "staff":
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    INSERT INTO users (name, email, phone, address, role, hashed_password, email_verified)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    form_data["name"],
                    form_data["email"],
                    form_data["phone"],
                    form_data["address"],
                    "staff",
                    hashed_password,
                    1
                ))
                cursor.execute("""
                    INSERT INTO staff (
                        name, email, contact, age, gender,
                        religion, address, education, aadhar, pan
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    form_data["name"],
                    form_data["email"],
                    form_data["phone"],
                    form_data["age"] or None,
                    form_data["gender"],
                    form_data["religion"],
                    form_data["address"],
                    form_data["education"],
                    form_data["aadhar"],
                    form_data["pan"]
                ))

            db.commit()
            cursor.close()

            return render_template(
                "register.html",
                success="Account created successfully. You can login now."
            )

        except Exception as e:
            db.rollback()
            return render_template(
                "register.html",
                error=f"Registration failed: {e}",
                form=form_data
            )

    return render_template("register.html")
# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= PROFILE =================
def ensure_profile_management_schema():
    if app.config.get("PROFILE_MANAGEMENT_SCHEMA_READY"):
        return

    db = get_db()
    cursor = db.cursor()

    user_columns = [
        "ADD COLUMN profile_image VARCHAR(255) NULL",
        "ADD COLUMN mobile_verified TINYINT(1) DEFAULT 0",
        "ADD COLUMN emergency_contact_name VARCHAR(255) NULL",
        "ADD COLUMN emergency_contact_phone VARCHAR(40) NULL",
        "ADD COLUMN emergency_contact_relation VARCHAR(80) NULL",
    ]

    for column_sql in user_columns:
        try:
            cursor.execute(f"ALTER TABLE users {column_sql}")
        except mysql.connector.Error:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_addresses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            label VARCHAR(80) NOT NULL,
            recipient_name VARCHAR(255) NOT NULL,
            phone VARCHAR(40) NOT NULL,
            address TEXT NOT NULL,
            is_default TINYINT(1) DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_delivery_addresses_user (user_id, is_default)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            relation VARCHAR(80) NOT NULL,
            age INT NULL,
            notes TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_family_members_user (user_id)
        )
    """)

    db.commit()
    cursor.close()
    app.config["PROFILE_MANAGEMENT_SCHEMA_READY"] = True


def get_profile_context(user_id):
    ensure_profile_management_schema()
    db = get_db()

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM delivery_addresses
        WHERE user_id=%s
        ORDER BY is_default DESC, id DESC
    """, (user_id,))
    addresses = cursor.fetchall()
    cursor.close()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM family_members
        WHERE user_id=%s
        ORDER BY id DESC
    """, (user_id,))
    family_members = cursor.fetchall()
    cursor.close()

    return user, addresses, family_members


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    user, addresses, family_members = get_profile_context(session["user"]["id"])
    return render_template(
        "profile.html",
        user=user,
        addresses=addresses,
        family_members=family_members
    )


@app.route("/profile/photo", methods=["POST"])
def update_profile_photo():
    if "user" not in session:
        return redirect("/login")

    ensure_profile_management_schema()
    photo = request.files.get("profile_photo")

    if not photo or not photo.filename:
        return redirect("/profile")

    allowed_extensions = {"jpg", "jpeg", "png", "webp"}
    extension = photo.filename.rsplit(".", 1)[-1].lower() if "." in photo.filename else ""

    if extension not in allowed_extensions:
        return redirect("/profile")

    host_static_root = os.environ.get("HOST_STATIC_ROOT")
    if not host_static_root and os.path.isdir("/home/admin/YuvrajMedical/static"):
        host_static_root = "/home/admin/YuvrajMedical/static"

    static_root = host_static_root or os.path.join(app.root_path, "static")
    upload_dir = os.path.join(static_root, "profile_photos")
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(f"user_{session['user']['id']}_{secrets.token_hex(6)}.{extension}")
    photo.save(os.path.join(upload_dir, filename))
    image_path = f"profile_photos/{filename}"

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET profile_image=%s WHERE id=%s",
        (image_path, session["user"]["id"])
    )
    db.commit()
    cursor.close()

    return redirect("/profile")


@app.route("/profile/manage/<section>", methods=["GET", "POST"])
def profile_manage(section):
    if "user" not in session:
        return redirect("/login")

    valid_sections = {
        "change_password",
        "change_mobile",
        "verify_mobile",
        "verify_email",
        "addresses",
        "family",
        "emergency",
    }
    if section not in valid_sections:
        return redirect("/profile")

    user_id = session["user"]["id"]
    db = get_db()
    message = None
    error = None

    if request.method == "POST":
        try:
            if section == "change_password":
                current_password = request.form.get("current_password", "")
                new_password = request.form.get("new_password", "")
                confirm_password = request.form.get("confirm_password", "")

                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
                user = cursor.fetchone()

                password_ok = False
                if user.get("hashed_password"):
                    password_ok = check_password_hash(user["hashed_password"], current_password)
                elif user.get("password") == current_password:
                    password_ok = True

                if not password_ok:
                    error = "Current password is incorrect."
                elif len(new_password) < 6:
                    error = "New password must be at least 6 characters."
                elif new_password != confirm_password:
                    error = "New password and confirmation do not match."
                else:
                    cursor.execute("""
                        UPDATE users
                        SET hashed_password=%s
                        WHERE id=%s
                    """, (generate_password_hash(new_password), user_id))
                    db.commit()
                    message = "Password changed successfully."
                cursor.close()

            elif section == "change_mobile":
                phone = request.form.get("phone", "").strip()
                if not normalize_fast2sms_number(phone):
                    error = "Enter a valid 10 digit mobile number."
                else:
                    cursor = db.cursor()
                    cursor.execute("""
                        UPDATE users
                        SET phone=%s, mobile_verified=0
                        WHERE id=%s
                    """, (phone, user_id))
                    db.commit()
                    cursor.close()
                    message = "Mobile number updated. Please verify it."

            elif section == "verify_mobile":
                action = request.form.get("action")
                user, _, _ = get_profile_context(user_id)
                if action == "send_otp":
                    otp = create_otp(db, user_id, user["email"], "verify_mobile")
                    sms_sent, sms_message = send_phone_otp(user["phone"], otp)
                    message = sms_message or "OTP sent to your mobile number."
                    if not sms_sent:
                        error = sms_message or "Could not send OTP."
                        message = None
                else:
                    otp = request.form.get("otp", "").strip()
                    if verify_otp(db, user["email"], "verify_mobile", otp):
                        cursor = db.cursor()
                        cursor.execute("UPDATE users SET mobile_verified=1 WHERE id=%s", (user_id,))
                        db.commit()
                        cursor.close()
                        message = "Mobile number verified successfully."
                    else:
                        error = "Invalid or expired mobile OTP."

            elif section == "verify_email":
                action = request.form.get("action")
                user, _, _ = get_profile_context(user_id)
                if action == "send_otp":
                    otp = create_otp(db, user_id, user["email"], "verify_email")
                    message = f"Email verification OTP generated: {otp}"
                else:
                    otp = request.form.get("otp", "").strip()
                    if verify_otp(db, user["email"], "verify_email", otp):
                        cursor = db.cursor()
                        cursor.execute("UPDATE users SET email_verified=1 WHERE id=%s", (user_id,))
                        db.commit()
                        cursor.close()
                        message = "Email verified successfully."
                    else:
                        error = "Invalid or expired email OTP."

            elif section == "addresses":
                label = request.form.get("label", "").strip() or "Home"
                recipient_name = request.form.get("recipient_name", "").strip()
                phone = request.form.get("phone", "").strip()
                address = request.form.get("address", "").strip()
                is_default = 1 if request.form.get("is_default") == "on" else 0

                if not recipient_name or not phone or not address:
                    error = "Please fill recipient name, phone, and address."
                else:
                    cursor = db.cursor()
                    if is_default:
                        cursor.execute(
                            "UPDATE delivery_addresses SET is_default=0 WHERE user_id=%s",
                            (user_id,)
                        )
                    cursor.execute("""
                        INSERT INTO delivery_addresses
                            (user_id, label, recipient_name, phone, address, is_default)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (user_id, label, recipient_name, phone, address, is_default))
                    db.commit()
                    cursor.close()
                    message = "Delivery address added."

            elif section == "family":
                name = request.form.get("name", "").strip()
                relation = request.form.get("relation", "").strip()
                age = request.form.get("age", "").strip()
                notes = request.form.get("notes", "").strip()

                if not name or not relation:
                    error = "Please fill family member name and relation."
                else:
                    cursor = db.cursor()
                    cursor.execute("""
                        INSERT INTO family_members (user_id, name, relation, age, notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, name, relation, int(age) if age else None, notes or None))
                    db.commit()
                    cursor.close()
                    message = "Family member profile added."

            elif section == "emergency":
                name = request.form.get("name", "").strip()
                phone = request.form.get("phone", "").strip()
                relation = request.form.get("relation", "").strip()

                if not name or not phone:
                    error = "Please fill emergency contact name and phone."
                else:
                    cursor = db.cursor()
                    cursor.execute("""
                        UPDATE users
                        SET emergency_contact_name=%s,
                            emergency_contact_phone=%s,
                            emergency_contact_relation=%s
                        WHERE id=%s
                    """, (name, phone, relation, user_id))
                    db.commit()
                    cursor.close()
                    message = "Emergency contact updated."
        except Exception as e:
            db.rollback()
            error = f"Could not save changes: {e}"

    user, addresses, family_members = get_profile_context(user_id)
    return render_template(
        "profile_manage.html",
        section=section,
        user=user,
        addresses=addresses,
        family_members=family_members,
        message=message,
        error=error
    )

# ================= Edit Profile =========
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            UPDATE users
            SET name=%s, phone=%s, address=%s
            WHERE id=%s
        """, (name, phone, address, user_id))

        db.commit()
        cursor.close()

        return redirect("/profile")

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM users WHERE id=%s
    """, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return render_template("edit_profile.html", user=user)
# ================= CART =================
@app.route("/add/<int:id>")
def add_to_cart(id):

    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, prescription_required
        FROM medicines
        WHERE id=%s
    """, (id,))
    medicine = cursor.fetchone()
    cursor.close()

    if medicine and medicine["prescription_required"]:
        flash(f"{medicine['name']} requires prescription. Please upload prescription first.")
        return redirect("/upload_prescription")

    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT id, quantity
            FROM cart
            WHERE user_id=%s AND medicine_id=%s
        """, (user_id, id))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE cart
                SET quantity = quantity + 1
                WHERE user_id=%s AND medicine_id=%s
            """, (user_id, id))
        else:
            cursor.execute("""
                INSERT INTO cart (user_id, medicine_id, quantity)
                VALUES (%s, %s, %s)
            """, (user_id, id, 1))

        db.commit()
        cursor.close()

    except Exception as e:
        db.rollback()
        return f"Cart Error: {e}"

    return redirect(request.referrer or "/")
@app.route("/increase/<int:id>")
def increase(id):
    db = get_db()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, prescription_required
        FROM medicines
        WHERE id=%s
    """, (id,))
    medicine = cursor.fetchone()
    cursor.close()

    if medicine and medicine["prescription_required"]:
        flash(f"{medicine['name']} requires prescription. Please upload prescription first.")
        return redirect("/upload_prescription")
    if "user" not in session:
        return redirect("/login")
    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE cart
        SET quantity = quantity + 1
        WHERE user_id=%s AND medicine_id=%s
    """, (user_id, id))

    db.commit()
    cursor.close()
    return redirect(request.referrer or "/")


@app.route("/decrease/<int:id>")
def decrease(id):
    db = get_db()
    if "user" not in session:
         return redirect("/login")
    user_id = session["user"]["id"]

    cursor=db.cursor()
    cursor.execute("""
        UPDATE cart
        SET quantity = quantity - 1
        WHERE user_id=%s AND medicine_id=%s
    """, (user_id, id))

    cursor=db.cursor()
    cursor.execute("""
        DELETE FROM cart
        WHERE user_id=%s AND medicine_id=%s AND quantity <= 0
    """, (user_id, id))

    db.commit()
    cursor.close()
    return redirect(request.referrer or "/")


# ================= CART PAGE =================
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]


    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicines.id, medicines.name, medicines.price,
               cart.quantity
        FROM cart
        JOIN medicines ON medicines.id = cart.medicine_id
        WHERE cart.user_id=%s
    """, (user_id,))
    rows = cursor.fetchall()

    items = []
    total = 0

    for r in rows:
        subtotal = r["price"] * r["quantity"]
        total += subtotal

        items.append({
            "id": r["id"],
            "name": r["name"],
            "price": r["price"],
            "qty": r["quantity"],
            "subtotal": subtotal
        })
    cursor.close()
    return render_template("cart.html", items=items, total=total)


# ================= CHECKOUT =================
@app.route("/checkout")
def checkout():
    if "user" not in session:
        return redirect("/login")

    return render_template("checkout.html")

# ================= PLACE ORDER =================
# ================= PLACE ORDER =================
@app.route("/place_order", methods=["POST"])
def place_order():

    if "user" not in session:
        return redirect("/login")

    db = get_db()

    try:

        # ================= START TRANSACTION =================
        cursor = db.cursor(dictionary=True)
        cursor.execute("BEGIN")

        user_id = session["user"]["id"]

        # ================= PRESCRIPTION UPLOAD =================
        file = request.files.get("prescription")
        file_path = None

        if file and file.filename != "":

            upload_folder = os.path.join("static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)

            filename = secure_filename(
                f"{datetime.now().timestamp()}_{file.filename}"
            )

            file_path = os.path.join(upload_folder, filename)

            file.save(file_path)

        # ================= GET CART ITEMS =================

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT medicines.id,
                   medicines.name,
                   medicines.price,
                   medicines.stock,
                   cart.quantity
            FROM cart
            JOIN medicines
            ON medicines.id = cart.medicine_id
            WHERE cart.user_id=%s
        """, (user_id,))
        cart_items = cursor.fetchall()

        # ================= EMPTY CART =================
        if not cart_items:
            db.rollback()
            flash("Your cart is empty")
            return redirect("/cart")

        total = 0

        # ================= CHECK STOCK FIRST =================
        for item in cart_items:

            if item["quantity"] > item["stock"]:

                db.rollback()

                flash(
                    f"{item['name']} has only "
                    f"{item['stock']} item(s) left in stock"
                )

                return redirect("/cart")

        # ================= CREATE ORDER =================

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO orders (
                user_id,
                total,
                date,
                status,
                prescription
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            0,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Pending",
            file_path
        ))

        order_id = cursor.lastrowid

        # ================= PROCESS ITEMS =================
        for item in cart_items:

            subtotal = item["price"] * item["quantity"]

            total += subtotal

            # ================= SAVE ORDER ITEMS =================
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO order_items (
                    order_id,
                    medicine_id,
                    quantity,
                    price
                )
                VALUES (%s, %s, %s, %s)
            """, (
                order_id,
                item["id"],
                item["quantity"],
                item["price"]
            ))

            # ================= UPDATE STOCK =================
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                UPDATE medicines
                SET stock = stock - %s
                WHERE id=%s
            """, (
                item["quantity"],
                item["id"]
            ))

        # ================= UPDATE TOTAL =================
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            UPDATE orders
            SET total=%s
            WHERE id=%s
        """, (
            total,
            order_id
        ))

        # ================= CLEAR CART =================
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            DELETE FROM cart
            WHERE user_id=%s
        """, (user_id,))

        # ================= COMMIT =================
        db.commit()
        cursor.close()

        flash("Order placed successfully")

        return redirect("/my_orders")

    except Exception as e:

        db.rollback()

        print("PLACE ORDER ERROR:", e)

        flash(f"Order Failed: {e}")

        return redirect("/cart")

# ================= UPDATE MEDICINE IMAGE =================
@app.route("/update_image/<int:id>", methods=["POST"])
def update_image(id):

    if "user" not in session:
        return redirect("/login")

    file = request.files.get("image")

    if not file or file.filename == "":
        flash("No image selected")
        return redirect("/staff")

    try:

        image_url = save_image(file)

        if not image_url:
            flash("Cloudinary upload failed")
            return redirect("/staff")

        db = get_db()

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            UPDATE medicines
            SET image=%s
            WHERE id=%s
        """, (
            image_url,
            id
        ))

        db.commit()
        cursor.close()

        flash("Medicine image updated successfully")

    except Exception as e:

        flash(f"Upload failed: {e}")

    return redirect("/staff")
# ================= MY ORDERS =================
@app.route("/my_orders")
def my_orders():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]


    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
    """, (user_id,))
    orders_raw = cursor.fetchall()
    cursor.close()

    orders = []

    for o in orders_raw:

        cursor=db.cursor(dictionary=True)
        cursor.execute("""
            SELECT medicines.name, order_items.quantity, order_items.price
            FROM order_items
            JOIN medicines ON medicines.id = order_items.medicine_id
            WHERE order_items.order_id=%s
        """, (o["id"],))
        items = cursor.fetchall()
        cursor.close()
        orders.append({
            "order_id": o["id"],
            "total": o["total"],
            "date": o["date"],
            "status": o["status"],
            "items": items,
            "prescription": o["prescription"]
        })


    return render_template("my_orders.html", orders=orders)


def build_customer_dashboard_context(db, user_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 6
    """, (user_id,))
    orders_raw = cursor.fetchall()
    cursor.close()

    recent_orders = []
    for o in orders_raw:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT medicines.name, order_items.quantity, order_items.price
            FROM order_items
            JOIN medicines ON medicines.id = order_items.medicine_id
            WHERE order_items.order_id=%s
        """, (o["id"],))
        items = cursor.fetchall()
        cursor.close()
        recent_orders.append({
            "order_id": o["id"],
            "total": o["total"],
            "date": o["date"],
            "status": o["status"],
            "items": items,
            "prescription": o["prescription"]
        })

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(*) AS total_orders, COALESCE(SUM(total), 0) AS total_spent
        FROM orders
        WHERE user_id=%s
    """, (user_id,))
    order_summary = cursor.fetchone() or {"total_orders": 0, "total_spent": 0}
    cursor.close()

    prescription_summary = {
        "total": 0,
        "pending": 0,
        "approved": 0,
        "latest_status": "No prescriptions yet"
    }
    recent_prescriptions = []
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT *
            FROM prescription_requests
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 4
        """, (user_id,))
        recent_prescriptions = cursor.fetchall()
        cursor.close()

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Pending Review' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved
            FROM prescription_requests
            WHERE user_id=%s
        """, (user_id,))
        prescription_counts = cursor.fetchone() or {}
        cursor.close()

        prescription_summary = {
            "total": prescription_counts.get("total") or 0,
            "pending": prescription_counts.get("pending") or 0,
            "approved": prescription_counts.get("approved") or 0,
            "latest_status": recent_prescriptions[0]["status"] if recent_prescriptions else "No prescriptions yet"
        }
    except Exception:
        recent_prescriptions = []

    notifications = []
    if recent_orders:
        latest_order = recent_orders[0]
        notifications.append(f"Order #{latest_order['order_id']} is {latest_order['status']}.")
    if recent_prescriptions:
        latest_prescription = recent_prescriptions[0]
        notifications.append(f"Prescription request #{latest_prescription['id']} is {latest_prescription['status']}.")
    if not notifications:
        notifications.append("Upload a prescription or place an order to start tracking updates here.")

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, name, price, image
            FROM medicines
            WHERE stock > 0
            ORDER BY stock DESC, id DESC
            LIMIT 6
        """)
        featured_medicines = cursor.fetchall()
    except Exception:
        featured_medicines = []
    cursor.close()

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, price, image FROM medicines ORDER BY RAND() LIMIT 8")
        recommendations = cursor.fetchall()
    except Exception:
        recommendations = []
    cursor.close()

    return {
        "order_summary": order_summary,
        "prescription_summary": prescription_summary,
        "recent_prescriptions": recent_prescriptions,
        "recent_orders": recent_orders,
        "featured_medicines": featured_medicines,
        "notifications": notifications,
        "recommendations": recommendations
    }


# ================= CUSTOMER DASHBOARD (Premium) =================
@app.route("/customer_dashboard")
def customer_dashboard():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]

    # recent orders (limit 6)
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 6
    """, (user_id,))
    orders_raw = cursor.fetchall()
    cursor.close()

    recent_orders = []

    for o in orders_raw:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT medicines.name, order_items.quantity, order_items.price
            FROM order_items
            JOIN medicines ON medicines.id = order_items.medicine_id
            WHERE order_items.order_id=%s
        """, (o["id"],))
        items = cursor.fetchall()
        cursor.close()
        recent_orders.append({
            "order_id": o["id"],
            "total": o["total"],
            "date": o["date"],
            "status": o["status"],
            "items": items,
            "prescription": o["prescription"]
        })

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(*) AS total_orders, COALESCE(SUM(total), 0) AS total_spent
        FROM orders
        WHERE user_id=%s
    """, (user_id,))
    order_summary = cursor.fetchone() or {"total_orders": 0, "total_spent": 0}
    cursor.close()

    prescription_summary = {
        "total": 0,
        "pending": 0,
        "approved": 0,
        "latest_status": "No prescriptions yet"
    }
    recent_prescriptions = []
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT *
            FROM prescription_requests
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 4
        """, (user_id,))
        recent_prescriptions = cursor.fetchall()
        cursor.close()

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Pending Review' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved
            FROM prescription_requests
            WHERE user_id=%s
        """, (user_id,))
        prescription_counts = cursor.fetchone() or {}
        cursor.close()

        prescription_summary = {
            "total": prescription_counts.get("total") or 0,
            "pending": prescription_counts.get("pending") or 0,
            "approved": prescription_counts.get("approved") or 0,
            "latest_status": recent_prescriptions[0]["status"] if recent_prescriptions else "No prescriptions yet"
        }
    except Exception:
        recent_prescriptions = []

    notifications = []
    if recent_orders:
        latest_order = recent_orders[0]
        notifications.append(f"Order #{latest_order['order_id']} is {latest_order['status']}.")
    if recent_prescriptions:
        latest_prescription = recent_prescriptions[0]
        notifications.append(f"Prescription request #{latest_prescription['id']} is {latest_prescription['status']}.")
    if not notifications:
        notifications.append("Upload a prescription or place an order to start tracking updates here.")

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, name, price, image
            FROM medicines
            WHERE stock > 0
            ORDER BY stock DESC, id DESC
            LIMIT 6
        """)
        featured_medicines = cursor.fetchall()
    except Exception:
        featured_medicines = []
    cursor.close()

    # simple recommendations: random medicines
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, price, image FROM medicines ORDER BY RAND() LIMIT 8")
        recommendations = cursor.fetchall()
    except Exception:
        recommendations = []
    cursor.close()

    return render_template(
        "customer_dashboard.html",
        user=session["user"],
        order_summary=order_summary,
        prescription_summary=prescription_summary,
        recent_prescriptions=recent_prescriptions,
        recent_orders=recent_orders,
        featured_medicines=featured_medicines,
        notifications=notifications,
        recommendations=recommendations
    )


# ================= CANCEL ORDER =================
@app.route("/cancel_order/<int:order_id>")
def cancel_order(order_id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]


    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT status FROM orders
        WHERE id=%s AND user_id=%s
    """, (order_id, user_id))
    order = cursor.fetchone()
    cursor.close()
    if not order:
        return "Invalid order"

    if order["status"] == "Delivered":
        return "Cannot cancel delivered order"


    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicine_id, quantity
        FROM order_items
        WHERE order_id=%s
    """, (order_id,))
    items = cursor.fetchall()

    for item in items:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            UPDATE medicines
            SET stock = stock + %s
            WHERE id=%s
        """, (item["quantity"], item["medicine_id"]))
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE orders
        SET status='Cancelled'
        WHERE id=%s
    """, (order_id,))

    db.commit()
    cursor.close()
    return redirect("/my_orders")
# ================= DELIVER ORDER (ADD HERE) =================
@app.route("/deliver_order/<int:id>")
def deliver_order(id):
    if "user" not in session or session["user"]["role"] != "staff":
        return redirect("/login")

    db = get_db()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE orders
        SET status='Delivered'
        WHERE id=%s
    """, (id,))

    db.commit()
    cursor.close()

    return redirect("/staff")
# ================= OWNER DASHBOARD =================
@app.route("/owner_dashboard")
def owner_dashboard():

    if "user" not in session or session["user"]["role"] != "owner":
        return redirect("/login")

    db = get_db()

    # ================= DATES =================

    today = datetime.now().strftime("%Y-%m-%d")

    week_ago = (
        datetime.now() - timedelta(days=7)
    ).strftime("%Y-%m-%d")

    month_ago = (
        datetime.now() - timedelta(days=30)
    ).strftime("%Y-%m-%d")

    year_start = datetime.now().strftime("%Y-01-01")

    # ================= USER SEARCH =================

    user_search = request.args.get("user_search", "")

    if user_search:


        cursor = db.cursor(dictionary=True)
        cursor.execute("""

            SELECT * FROM users

            WHERE name LIKE %s
               OR email LIKE %s
               OR role LIKE %s

            ORDER BY id ASC

        """, (

            f"%{user_search}%",

            f"%{user_search}%",

            f"%{user_search}%"

        ))
        users_list = cursor.fetchall()
        cursor.close()

    else:


        cursor = db.cursor(dictionary=True)
        cursor.execute("""

            SELECT * FROM users
            ORDER BY id ASC

        """)
        users_list = cursor.fetchall()
        cursor.close()

    # ================= SALES =================


    cursor = db.cursor()
    cursor.execute("""

        SELECT COALESCE(SUM(total),0)

        FROM orders

        WHERE DATE(`date`) = %s
        AND status != 'Cancelled'

    """, (today,))
    today_sales = cursor.fetchone()[0]


    cursor = db.cursor()
    cursor.execute("""

        SELECT COALESCE(SUM(total),0)

        FROM orders

        WHERE date(date)>=date(%s)
        AND status != 'Cancelled'

    """, (week_ago,))
    weekly_sales = cursor.fetchone()[0]
    cursor.close()


    cursor = db.cursor()
    cursor.execute("""

        SELECT COALESCE(SUM(total),0)

        FROM orders

        WHERE date(date)>=date(%s)
        AND status != 'Cancelled'

    """, (month_ago,))
    monthly_sales = cursor.fetchone()[0]


    cursor = db.cursor()
    cursor.execute("""

        SELECT COALESCE(SUM(total),0)

        FROM orders

        WHERE date(date)>=date(%s)
        AND status != 'Cancelled'

    """, (year_start,))
    yearly_sales =cursor.fetchone()[0]
    cursor.close()

    # ================= ORDERS =================


    cursor = db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM orders

        WHERE status='Pending'

    """)
    pending_orders = cursor.fetchone()[0]
    cursor.close()


    cursor = db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM orders

        WHERE status='Delivered'

    """)
    success_orders = cursor.fetchone()[0]
    cursor.close()


    cursor =db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM orders

    """)
    total_orders =cursor.fetchone()[0]
    cursor.close()


    cursor = db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM orders

        WHERE status='Cancelled'

    """)
    cancelled_orders = cursor.fetchone()[0]
    cursor.close()
    # ================= USERS =================


    cursor = db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM users

        WHERE role='customer'

    """)
    total_users = cursor.fetchone()[0]
    cursor.close()

    # ================= MEDICINES =================


    cursor = db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM medicines

    """)
    total_medicines = cursor.fetchone()[0]
    cursor.close()


    cursor = db.cursor(dictionary=True)
    cursor.execute("""

        SELECT *
        FROM medicines
        ORDER BY id DESC

    """)
    medicines = cursor.fetchall()
    cursor.close()


    cursor =db.cursor(dictionary=True)
    cursor.execute("""

        SELECT *

        FROM medicines

        WHERE stock < 10

    """)
    low_stock = cursor.fetchall()
    cursor.close()


    cursor = db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM medicines

        WHERE stock=0

    """)
    out_of_stock = cursor.fetchone()[0]
    cursor.close()


    cursor = db.cursor(dictionary=True)
    cursor.execute("""

        SELECT *

        FROM medicines

        WHERE expiry_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)

    """)
    expiring =cursor.fetchall()
    cursor.close()

    # ================= STAFF =================


    cursor = db.cursor(dictionary=True)
    cursor.execute("""

        SELECT *

        FROM staff

    """)
    staff_list = cursor.fetchall()
    cursor.close()


    cursor =db.cursor()
    cursor.execute("""

        SELECT COUNT(*)

        FROM staff

    """)
    total_staff = cursor.fetchone()[0]
    cursor.close()

    # ================= RECENT ORDERS =================


    cursor =db.cursor(dictionary=True)
    cursor.execute("""

        SELECT orders.*,
               users.name AS customer_name

        FROM orders

        JOIN users
        ON users.id = orders.user_id

        ORDER BY orders.id DESC

        LIMIT 10

    """)
    recent_orders = cursor.fetchall()
    cursor.close()

    # ================= RENDER =================

    return render_template(

        "owner_dashboard.html",

        today_sales=today_sales,
        weekly_sales=weekly_sales,
        monthly_sales=monthly_sales,
        yearly_sales=yearly_sales,

        pending_orders=pending_orders,
        success_orders=success_orders,
        total_orders=total_orders,
        cancelled_orders=cancelled_orders,

        total_users=total_users,
        users_list=users_list,

        total_medicines=total_medicines,
        medicines=medicines,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        expiring=expiring,

        staff_list=staff_list,
        total_staff=total_staff,

        recent_orders=recent_orders
    )
# ================= STAFF DASHBOARD =================
@app.route("/staff")
def staff_dashboard():

    if "user" not in session:
        return redirect("/login")

    # allow BOTH owner and staff
    if session["user"]["role"] not in ["owner", "staff"]:
        return redirect("/")

    db = get_db()


    cursor =db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines")
    medicines = cursor.fetchall()
    cursor.close()


    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT orders.*, users.name AS customer_name
        FROM orders
        JOIN users ON users.id = orders.user_id
        ORDER BY orders.id DESC
    """)
    orders = cursor.fetchall()
    cursor.close()


    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM medicines WHERE stock < 10"
    )
    low_stock = cursor.fetchall()
    cursor.close()

    # ================= REAL DASHBOARD STATS =================


    cursor=db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )
    total_orders =cursor.fetchone()[0]
    cursor.close()


    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE status='Pending'"
    )
    pending_orders = cursor.fetchone()[0]
    cursor.close()


    cursor =db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE status='Delivered'"
    )
    delivered_orders =cursor.fetchone()[0]
    cursor.close()

    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM medicines"
        )
    total_medicines = cursor.fetchone()[0]
    cursor.close()

    return render_template(
        "staff.html",
        medicines=medicines,
        orders=orders,
        low_stock=low_stock,

        # 🔥 SEND REAL VALUES TO HTML
        total_orders=total_orders,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
        total_medicines=total_medicines
    )

#---------- ADD MEDICINE -------------
#----------medicine function-------------
@app.route("/add_medicine", methods=["POST"])
def add_medicine():
    
    department = request.form.get("department") or "General"
    if "user" not in session:
        return redirect("/login")

    db = get_db()

    try:

        name = request.form.get("name")
        department, prescription_required = classify_medicine(name)
        category = normalize_category(request.form.get("category"))
        price = request.form.get("price")
        stock = request.form.get("stock")
        expiry = request.form.get("expiry")
        barcode_number = request.form.get("barcode")
 
        image_url = None

        # ================= IMAGE UPLOAD =================

        file = request.files.get("image")

        if file and file.filename != "":

            image_url = save_image(file)

            if not image_url:
                flash("Image upload failed")

        # ================= BARCODE IMAGE GENERATE =================

        if barcode_number:
            generate_barcode_image(barcode_number)

        # ================= INSERT =================

        cursor = db.cursor(dictionary=True)
        cursor.execute("""

            INSERT INTO medicines
            (
                name,
                category,
                department,
                price,
                prescription_required,
                stock,
                expiry_date,
                image,
                barcode
            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

        """, (

            name,
            category,
            department,
            price,
            prescription_required,
            stock,
            expiry,
            image_url,
            barcode_number

        ))

        db.commit()
        cursor.close()
        flash("Medicine Added Successfully")

    except Exception as e:

        db.rollback()

        print("ADD MEDICINE ERROR:", e)

        flash(f"Error: {e}")

    return redirect("/staff")
#------------bulk upload medicine-----------
@app.route("/bulk_upload", methods=["POST"])
def bulk_upload():
    db = get_db()
    if "user" not in session:
        return redirect("/login")

    if session["user"]["role"] not in ["owner","staff"]:
       return redirect("/")
    try:
        file = request.files.get("file")

        if not file:
            return "No file selected"

        df = pd.read_excel(file)

        inserted = 0
        skipped = 0

        for _, row in df.iterrows():

            # ---------------- CLEAN DATA ----------------
            name = str(row.get("name", "")).strip()
            if not name:
                continue

            try:
                price = float(row.get("price", 0))
            except:
                price = 0

            try:
                stock_raw = str(row.get("stock", 0))
                stock = int(stock_raw.split(",")[0])
            except:
                stock = 0

            category = normalize_category(row.get("category", ""))
            expiry = str(row.get("expiry", "")).strip()
            department, prescription_required = classify_medicine(name)

            # ---------------- DUPLICATE CHECK ----------------

            cursor = db.cursor()
            cursor.execute(
                "SELECT id FROM medicines WHERE LOWER(name)=LOWER(%s)",
                (name,)
            )
            existing = cursor.fetchone()
            cursor.close()

            if existing:
                skipped += 1
                continue

            # ---------------- INSERT ----------------
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO medicines (name, price, stock, category, department, prescription_required, expiry_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, price, stock, category, department, prescription_required, expiry))

            inserted += 1

        db.commit()
        cursor.close()

        # ---------------- MESSAGE ----------------
        flash(f"{inserted} medicines uploaded successfully, {skipped} skipped (duplicates)")

        return redirect("/staff")

    except Exception as e:
        db.rollback()
        return f"Upload failed: {e}"
#-----------edit medicine fuc------
@app.route("/edit_medicine/<int:id>", methods=["POST"])
def edit_medicine(id):
    db = get_db()
    data = request.form
    if "user" not in session:
        return redirect("/login")

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE medicines
        SET name=%s, price=%s, stock=%s, category=%s, expiry_date=%s
        WHERE id=%s
    """, (
        data["name"],
        data["price"],
        data["stock"],
        normalize_category(data.get("category")),
        data["expiry"],
        id
    ))

    db.commit()
    cursor.close()
    return redirect("/staff")
#------------del medicine fuc---------
@app.route("/delete_medicine/<int:id>")
def delete_medicine(id):
    db = get_db()
    if "user" not in session:
        return redirect("/login")

    cursor = db.cursor(dictionary=True)
    cursor.execute("DELETE FROM medicines WHERE id=%s", (id,))
    db.commit()
    cursor.close()

    return redirect("/staff")

# ================= REMOVE STAFF =================
@app.route("/remove_staff/<int:id>")
def remove_staff(id):

    if "user" not in session or session["user"]["role"] != "owner":
        return redirect("/login")

    db = get_db()

    # get staff email

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT email FROM staff WHERE id=%s",
        (id,)
    )
    staff =cursor.fetchone()
    if staff:

        # remove from staff table
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "DELETE FROM staff WHERE id=%s",
            (id,)
        )

        # remove from users table
        cursor =db.cursor()
        cursor.execute(
            "DELETE FROM users WHERE email=%s",
            (staff["email"],)
        )

        db.commit()
        cursor.close()

    return redirect("/owner_dashboard")
# ================= BARCODE SCANNER =================
@app.route("/scan_barcode")
def scan_barcode():

    if "user" not in session:
        return redirect("/login")

    if session["user"]["role"] not in ["owner", "staff"]:
        return redirect("/")

    return render_template("scan_barcode.html")


@app.route("/barcode_result/<barcode>")
def barcode_result(barcode):

    if "user" not in session:
        return redirect("/login")

    if session["user"]["role"] not in ["owner", "staff"]:
        return redirect("/")

    db = get_db()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM medicines
        WHERE barcode=%s
    """, (barcode,))
    medicine = cursor.fetchone()
    cursor.close()

    if medicine:
        return render_template("barcode_result.html", medicine=medicine)

    return redirect(f"/add_scanned_medicine/{barcode}")


@app.route("/add_scanned_medicine/<barcode>", methods=["GET", "POST"])
def add_scanned_medicine(barcode):

    if "user" not in session:
        return redirect("/login")

    if session["user"]["role"] not in ["owner", "staff"]:
        return redirect("/")

    db = get_db()

    if request.method == "POST":

        try:
            name = request.form.get("name")
            category = normalize_category(request.form.get("category"))
            price = request.form.get("price")
            stock = request.form.get("stock")
            expiry = request.form.get("expiry")
            barcode_number = request.form.get("barcode")

            if barcode_number:
                generate_barcode_image(barcode_number)

            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO medicines
                (
                    name,
                    category,
                    price,
                    stock,
                    expiry_date,
                    barcode
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                name,
                category,
                price,
                stock,
                expiry,
                barcode_number
            ))

            db.commit()
            cursor.close()

            flash("New scanned medicine added successfully")
            return redirect("/staff")

        except Exception as e:
            db.rollback()
            flash(f"Error: {e}")
            return redirect(f"/add_scanned_medicine/{barcode}")

    return render_template("add_scanned_medicine.html", barcode=barcode)
# ================= GENERATE BARCODES FOR EXISTING MEDICINES =================
@app.route("/generate_all_barcodes")
def generate_all_barcodes():

    if "user" not in session:
        return redirect("/login")

    if session["user"]["role"] not in ["owner", "staff"]:
        return redirect("/")

    db = get_db()

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, barcode
            FROM medicines
            WHERE barcode IS NULL OR barcode=''
        """)
        medicines = cursor.fetchall()
        cursor.close()

        updated = 0

        for med in medicines:
            barcode_number = f"YM{str(med['id']).zfill(6)}"

            generate_barcode_image(barcode_number)

            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                UPDATE medicines
                SET barcode=%s
                WHERE id=%s
            """, (
                barcode_number,
                med["id"]
            ))

            updated += 1

        db.commit()
        cursor.close()

        flash(f"{updated} barcodes generated successfully")

    except Exception as e:
        db.rollback()
        flash(f"Barcode generation failed: {e}")

    return redirect("/staff#inventory")

# ================= Prescription Medicine Detection =================
def detect_medicines_from_text(text):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT name FROM medicines")
    medicines = cursor.fetchall()
    cursor.close()

    matches = []
    text = text.lower()

    lines = text.splitlines()

    for med in medicines:

        if not med["name"]:
            continue

        med_name = med["name"].lower()

        best_score = 0

        for line in lines:
            line = line.strip().lower()

            if not line:
                continue

            score = fuzz.partial_ratio(med_name, line)

            if score > best_score:
                best_score = score

        if best_score >= 85:
            matches.append({
                "medicine": med["name"],
                "score": round(best_score, 2)
            })

    matches.sort(key=lambda x: x["score"], reverse=True)

    return matches
# ================= Upload Prescription =================

@app.route("/upload_prescription", methods=["GET", "POST"])
def upload_prescription():
    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]["id"]

    if request.method == "POST":
        prescription = request.files.get("prescription")

        if not prescription or prescription.filename == "":
            flash("Please upload a prescription image", "error")
            return redirect("/upload_prescription")

        allowed_extensions = {"png", "jpg", "jpeg", "webp"}

        filename = secure_filename(prescription.filename)
        ext = filename.rsplit(".", 1)[-1].lower()

        if ext not in allowed_extensions:
            flash("Only PNG, JPG, JPEG, and WEBP files are allowed", "error")
            return redirect("/upload_prescription")

        os.makedirs(PRESCRIPTION_FOLDER, exist_ok=True)

        new_filename = f"user_{user_id}_{datetime.now().timestamp()}_{filename}"
        save_path = os.path.join(PRESCRIPTION_FOLDER, new_filename)

        prescription.save(save_path)

        ocr_text = read_prescription_text(save_path)

        if not ocr_text or len(ocr_text.strip()) < 5:
            ocr_text = "OCR could not clearly read this prescription. Manual staff review required."

        detected_medicines = detect_medicines_from_text(ocr_text)

        detected_text = ", ".join(
            [f"{m['medicine']} ({m['score']}%)" for m in detected_medicines]
        )

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO prescription_requests
            (user_id, prescription_image, ocr_text, detected_medicines, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            new_filename,
            ocr_text,
            detected_text,
            "Pending Review"
        ))

        db.commit()
        cursor.close()

        flash("Prescription uploaded successfully. Staff will review it shortly.", "success")
        return redirect("/my_prescriptions")

    return render_template("upload_prescription.html")
# ====================== customer prescription status =======================
@app.route("/my_prescriptions")
def my_prescriptions():
    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]["id"]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM prescription_requests
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    requests_data = cursor.fetchall()
    cursor.close()

    return render_template("my_prescriptions.html", requests_data=requests_data)
# ============================ checkout prescription ===============================
@app.route("/checkout_prescription/<int:request_id>")
def checkout_prescription(request_id):

    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM prescription_requests
        WHERE id=%s
        AND user_id=%s
        AND status='Approved'
    """, (request_id, user_id))

    prescription = cursor.fetchone()
    cursor.close()

    if not prescription:
        flash("Invalid prescription checkout")
        return redirect("/my_prescriptions")

    return render_template(
        "checkout_prescription.html",
        prescription=prescription
    )
# =============================== checkout prescription to cart =======================
@app.route("/add_prescription_to_cart/<int:request_id>")
def add_prescription_to_cart(request_id):

    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT approved_medicines
        FROM prescription_requests
        WHERE id=%s
        AND user_id=%s
        AND status='Approved'
    """, (request_id, user_id))

    prescription = cursor.fetchone()

    if not prescription or not prescription["approved_medicines"]:
        flash("No approved medicines found")
        cursor.close()
        return redirect("/my_prescriptions")

    medicine_names = [
        x.strip()
        for x in prescription["approved_medicines"].split(",")
        if x.strip()
    ]

    added = 0

    for med_name in medicine_names:

        cursor.execute("""
            SELECT id, stock
            FROM medicines
            WHERE LOWER(name)=LOWER(%s)
            LIMIT 1
        """, (med_name,))

        medicine = cursor.fetchone()

        if not medicine:
            continue

        if medicine["stock"] <= 0:
            continue

        cursor.execute("""
            SELECT id
            FROM cart
            WHERE user_id=%s AND medicine_id=%s
        """, (user_id, medicine["id"]))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE cart
                SET quantity = quantity + 1
                WHERE user_id=%s AND medicine_id=%s
            """, (user_id, medicine["id"]))
        else:
            cursor.execute("""
                INSERT INTO cart (user_id, medicine_id, quantity)
                VALUES (%s, %s, %s)
            """, (user_id, medicine["id"], 1))

        added += 1

    db.commit()
    cursor.close()

    flash(f"{added} approved medicines added to cart")
    return redirect("/cart")
# ========================== staff priscription request =============================
@app.route("/staff_prescriptions")
def staff_prescriptions():
    if "user" not in session:
        return redirect("/login")

    if session["user"]["role"] not in ["staff", "owner"]:
        return redirect("/")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT pr.*,
               u.name AS customer_name,
               u.email AS customer_email,
               u.phone AS customer_phone
        FROM prescription_requests pr
        JOIN users u ON pr.user_id = u.id
        ORDER BY pr.created_at DESC
    """)

    requests_data = cursor.fetchall()
    cursor.close()

    return render_template("staff_prescriptions.html", requests_data=requests_data)
# ================================== approve/reject route ==============================
@app.route("/review_prescription/<int:request_id>", methods=["POST"])
def review_prescription(request_id):

    if "user" not in session:
        return redirect("/login")

    if session["user"]["role"] not in ["staff", "owner"]:
        return redirect("/")

    action = request.form.get("action")
    staff_note = request.form.get("staff_note", "")

    if action not in ["Approved", "Rejected"]:
        flash("Invalid action", "error")
        return redirect("/staff_prescriptions")

    db = get_db()

    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM prescription_requests
            WHERE id=%s
        """, (request_id,))

        prescription = cursor.fetchone()

        if not prescription:
            flash("Prescription request not found", "error")
            cursor.close()
            return redirect("/staff_prescriptions")

        if action == "Rejected":
            cursor.execute("""
                UPDATE prescription_requests
                SET status=%s,
                    staff_note=%s,
                    reviewed_at=NOW()
                WHERE id=%s
            """, (
                "Rejected",
                staff_note,
                request_id
            ))

            db.commit()
            cursor.close()

            flash("Prescription rejected successfully", "success")
            return redirect("/staff_prescriptions")

        selected_medicines = request.form.getlist("selected_medicines")
        manual_medicines = request.form.get("manual_medicines", "")

        medicine_names = []

        for item in selected_medicines:
            clean_name = item.strip()

            if "(" in clean_name:
                clean_name = clean_name.split("(")[0].strip()

            if clean_name:
                medicine_names.append(clean_name)

        for item in manual_medicines.split(","):
            clean_name = item.strip()

            if clean_name:
                medicine_names.append(clean_name)

        if not medicine_names:
            flash("Please select at least one medicine before approval.", "error")
            cursor.close()
            return redirect("/staff_prescriptions")

        approved_text = ", ".join(medicine_names)

        cursor.execute("""
            UPDATE prescription_requests
            SET status=%s,
                staff_note=%s,
                approved_medicines=%s,
                reviewed_at=NOW()
            WHERE id=%s
        """, (
            "Approved",
            staff_note,
            approved_text,
            request_id
        ))

        db.commit()
        cursor.close()

        flash("Prescription approved. Customer can now proceed to checkout.", "success")
        return redirect("/staff_prescriptions")

    except Exception as e:
        db.rollback()
        flash(f"Review failed: {e}", "error")
        return redirect("/staff_prescriptions")
# ================= Types of medicines ================
@app.route("/type/<medicine_type>")
def medicine_type_page(medicine_type):

    if "user" not in session:
        return redirect("/login")

    db = get_db()

    cursor = db.cursor(dictionary=True)
    basic_type = next(
        (item for item in BASIC_MEDICINE_TYPES if item["name"] == medicine_type),
        None
    )

    if basic_type:
        placeholders = ", ".join(["%s"] * len(basic_type["aliases"]))
        cursor.execute(f"""
            SELECT *
            FROM medicines
            WHERE category IN ({placeholders})
            ORDER BY name ASC
        """, tuple(basic_type["aliases"]))
    elif medicine_type == "General":
        cursor.execute("""
            SELECT *
            FROM medicines
            WHERE category=%s
               OR category IS NULL
               OR TRIM(category) = ''
            ORDER BY name ASC
        """, (medicine_type,))
    else:
        cursor.execute("""
            SELECT *
            FROM medicines
            WHERE category=%s
            ORDER BY name ASC
        """, (medicine_type,))
    medicines = cursor.fetchall()
    cursor.close()

    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicine_id, quantity
        FROM cart
        WHERE user_id=%s
    """, (user_id,))
    cart_rows = cursor.fetchall()
    cursor.close()

    cart = {str(r["medicine_id"]): r["quantity"] for r in cart_rows}
    cart_count = sum(cart.values())

    return render_template(
        "department.html",
        medicines=medicines,
        dept_name=medicine_type,
        cart=cart,
        cart_count=cart_count
    )
#==========testing================

# ================= RUN =================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
