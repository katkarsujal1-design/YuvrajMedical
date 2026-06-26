from flask import Flask, render_template, request, redirect, session, g, jsonify, send_from_directory, abort, make_response
#import pymysql
import base64
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
from urllib.parse import quote
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


@app.context_processor
def inject_site_header_context():
    user = session.get("user")
    if not user:
        return {"cart_count": 0, "notifications": [], "notification_items": [], "notification_unread_count": 0}

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT COALESCE(SUM(quantity),0) AS count FROM cart WHERE user_id=%s", (user["id"],))
        cart_count = (cursor.fetchone() or {}).get("count", 0)
        cursor.close()

        notification_items, notification_unread_count = get_user_notifications(user["id"], limit=6)
        notifications = [item["message"] for item in notification_items]
        if not notification_items:
            notifications.append("Upload a prescription or place an order to start tracking updates here.")
        return {
            "cart_count": cart_count,
            "notifications": notifications,
            "notification_items": notification_items,
            "notification_unread_count": notification_unread_count,
        }
    except Exception:
        return {"cart_count": 0, "notifications": [], "notification_items": [], "notification_unread_count": 0}


ORDER_STATUSES = [
    "Pending",
    "Approved",
    "Packed",
    "Out For Delivery",
    "Delivered",
    "Cancelled",
    "Refunded",
]

ORDER_STATUS_STEPS = [
    "Pending",
    "Approved",
    "Packed",
    "Out For Delivery",
    "Delivered",
]

PAYMENT_METHODS = [
    "UPI",
    "Google Pay",
    "PhonePe",
    "Paytm",
    "Cash On Delivery",
    "Wallet Balance",
]

MANUAL_PAYMENT_METHODS = ["UPI", "Google Pay", "PhonePe", "Paytm"]

NOTIFICATION_TYPES = {
    "Order Updates": "Order status and fulfillment progress",
    "Prescription Updates": "Prescription upload and review updates",
    "Delivery Updates": "Delivery OTP, courier, and live status updates",
    "Offer Notifications": "Savings and monthly health offers",
    "Refill Reminders": "Repeat medicine and refill reminders",
    "Expiry Reminders": "Medicine expiry reminders",
    "Health Tips Notifications": "Short wellness and safety tips",
}

REVIEW_TYPES = [
    "Medicine Rating",
    "Order Review",
    "Delivery Experience",
    "Issue Report",
]


def ensure_order_management_schema():
    if app.config.get("ORDER_MANAGEMENT_SCHEMA_READY"):
        return

    db = get_db()
    cursor = db.cursor()
    for column_sql in [
        "ADD COLUMN return_status VARCHAR(40) DEFAULT 'Not Requested'",
        "ADD COLUMN refund_status VARCHAR(40) DEFAULT 'Not Applicable'",
    ]:
        try:
            cursor.execute(f"ALTER TABLE orders {column_sql}")
        except mysql.connector.Error:
            pass
    db.commit()
    cursor.close()
    app.config["ORDER_MANAGEMENT_SCHEMA_READY"] = True


def ensure_delivery_feature_schema():
    if app.config.get("DELIVERY_FEATURE_SCHEMA_READY"):
        return

    ensure_order_management_schema()
    db = get_db()
    cursor = db.cursor()
    delivery_columns = [
        "ADD COLUMN delivery_status VARCHAR(80) DEFAULT 'Pending'",
        "ADD COLUMN delivery_otp VARCHAR(10) NULL",
        "ADD COLUMN delivery_notes TEXT NULL",
        "ADD COLUMN delivery_address TEXT NULL",
        "ADD COLUMN courier_name VARCHAR(120) NULL",
        "ADD COLUMN courier_tracking_id VARCHAR(120) NULL",
        "ADD COLUMN courier_tracking_url VARCHAR(255) NULL",
        "ADD COLUMN delivery_updated_at DATETIME NULL",
    ]
    for column_sql in delivery_columns:
        try:
            cursor.execute(f"ALTER TABLE orders {column_sql}")
        except mysql.connector.Error:
            pass
    try:
        cursor.execute("""
            UPDATE orders
            SET delivery_otp = LPAD(FLOOR(RAND() * 1000000), 6, '0')
            WHERE delivery_otp IS NULL OR delivery_otp=''
        """)
        cursor.execute("""
            UPDATE orders
            SET delivery_status = CASE
                WHEN status='Pending' THEN 'Order Received'
                WHEN status='Approved' THEN 'Delivery Scheduled'
                WHEN status='Packed' THEN 'Packed For Pickup'
                WHEN status='Out For Delivery' THEN 'Out For Delivery'
                WHEN status='Delivered' THEN 'Delivered'
                WHEN status='Cancelled' THEN 'Delivery Cancelled'
                WHEN status='Refunded' THEN 'Refunded'
                ELSE 'Order Received'
            END
            WHERE delivery_status IS NULL OR delivery_status=''
        """)
        cursor.execute("""
            UPDATE orders
            SET courier_tracking_id = CONCAT('YMD', LPAD(id, 6, '0'))
            WHERE courier_tracking_id IS NULL OR courier_tracking_id=''
        """)
        cursor.execute("""
            UPDATE orders
            SET courier_name = 'Yuvraj Local Delivery'
            WHERE courier_name IS NULL OR courier_name=''
        """)
    except mysql.connector.Error:
        pass
    db.commit()
    cursor.close()
    app.config["DELIVERY_FEATURE_SCHEMA_READY"] = True


def ensure_payment_schema():
    if app.config.get("PAYMENT_SCHEMA_READY"):
        return

    ensure_delivery_feature_schema()
    db = get_db()
    cursor = db.cursor()
    for column_sql in [
        "ADD COLUMN payment_method VARCHAR(80) DEFAULT 'Cash On Delivery'",
        "ADD COLUMN payment_status VARCHAR(80) DEFAULT 'Pending'",
        "ADD COLUMN payment_reference VARCHAR(160) NULL",
        "ADD COLUMN payment_screenshot VARCHAR(255) NULL",
    ]:
        try:
            cursor.execute(f"ALTER TABLE orders {column_sql}")
        except mysql.connector.Error:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            user_id INT NOT NULL,
            method VARCHAR(80) NOT NULL,
            amount DECIMAL(10,2) NOT NULL DEFAULT 0,
            transaction_id VARCHAR(160),
            screenshot VARCHAR(255),
            status VARCHAR(80) NOT NULL DEFAULT 'Pending Verification',
            notes TEXT,
            created_at DATETIME,
            verified_at DATETIME,
            verified_by INT,
            INDEX(order_id),
            INDEX(user_id)
        )
    """)
    db.commit()
    cursor.close()
    app.config["PAYMENT_SCHEMA_READY"] = True


def ensure_notification_schema():
    if app.config.get("NOTIFICATION_SCHEMA_READY"):
        return

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type VARCHAR(80) NOT NULL,
            title VARCHAR(180) NOT NULL,
            message TEXT NOT NULL,
            target_url VARCHAR(255),
            dedupe_key VARCHAR(190) NOT NULL,
            is_read TINYINT(1) NOT NULL DEFAULT 0,
            created_at DATETIME,
            UNIQUE KEY unique_notification_dedupe (dedupe_key),
            INDEX(user_id),
            INDEX(type),
            INDEX(is_read)
        )
    """)
    db.commit()
    cursor.close()
    app.config["NOTIFICATION_SCHEMA_READY"] = True


def ensure_reviews_feedback_schema():
    if app.config.get("REVIEWS_FEEDBACK_SCHEMA_READY"):
        return

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews_feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            review_type VARCHAR(80) NOT NULL,
            medicine_id INT NULL,
            order_id INT NULL,
            rating INT NULL,
            title VARCHAR(180),
            message TEXT NOT NULL,
            issue_category VARCHAR(120),
            status VARCHAR(60) NOT NULL DEFAULT 'Submitted',
            created_at DATETIME,
            INDEX(user_id),
            INDEX(medicine_id),
            INDEX(order_id),
            INDEX(review_type)
        )
    """)
    db.commit()
    cursor.close()
    app.config["REVIEWS_FEEDBACK_SCHEMA_READY"] = True


def add_notification(user_id, notification_type, title, message, target_url, dedupe_key):
    ensure_notification_schema()
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT IGNORE INTO notifications (
                user_id,
                type,
                title,
                message,
                target_url,
                dedupe_key,
                is_read,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, 0, %s)
        """, (
            user_id,
            notification_type,
            title,
            message,
            target_url,
            dedupe_key,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()
    except mysql.connector.Error:
        db.rollback()
    finally:
        cursor.close()


def sync_user_notifications(user_id):
    ensure_notification_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, status, delivery_status, courier_tracking_id
        FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    latest_order = cursor.fetchone()
    if latest_order:
        add_notification(
            user_id,
            "Order Updates",
            f"Order #{latest_order['id']} is {latest_order['status']}",
            f"Your medicine order is currently marked as {latest_order['status']}.",
            f"/order_details/{latest_order['id']}",
            f"order:{user_id}:{latest_order['id']}:{latest_order['status']}"
        )
        delivery_status = latest_order.get("delivery_status") or latest_order["status"]
        add_notification(
            user_id,
            "Delivery Updates",
            f"Delivery update for Order #{latest_order['id']}",
            f"Live delivery status: {delivery_status}. Tracking ID: {latest_order.get('courier_tracking_id') or 'Not assigned yet'}.",
            f"/order_tracking/{latest_order['id']}",
            f"delivery:{user_id}:{latest_order['id']}:{delivery_status}"
        )

    try:
        cursor.execute("""
            SELECT id, status
            FROM prescription_requests
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        latest_prescription = cursor.fetchone()
    except mysql.connector.Error:
        latest_prescription = None
    if latest_prescription:
        add_notification(
            user_id,
            "Prescription Updates",
            f"Prescription #{latest_prescription['id']} is {latest_prescription['status']}",
            "Your uploaded prescription review status has been updated.",
            "/my_prescriptions",
            f"prescription:{user_id}:{latest_prescription['id']}:{latest_prescription['status']}"
        )

    add_notification(
        user_id,
        "Offer Notifications",
        "Monthly medicine saver offer",
        "Explore monthly refill essentials, budget picks, and combo savings curated for your basket.",
        "/#offers",
        f"offer:{user_id}:monthly-saver"
    )

    cursor.execute("""
        SELECT id, date
        FROM orders
        WHERE user_id=%s
          AND status='Delivered'
          AND date <= DATE_SUB(NOW(), INTERVAL 25 DAY)
        ORDER BY date DESC
        LIMIT 1
    """, (user_id,))
    refill_order = cursor.fetchone()
    if refill_order:
        add_notification(
            user_id,
            "Refill Reminders",
            f"Refill reminder for Order #{refill_order['id']}",
            "It may be time to reorder routine medicines from your delivered order.",
            f"/reorder/{refill_order['id']}",
            f"refill:{user_id}:{refill_order['id']}"
        )

    cursor.execute("""
        SELECT medicines.name, medicines.expiry_date
        FROM order_items
        JOIN orders ON orders.id = order_items.order_id
        JOIN medicines ON medicines.id = order_items.medicine_id
        WHERE orders.user_id=%s
          AND medicines.expiry_date IS NOT NULL
          AND medicines.expiry_date >= CURDATE()
          AND medicines.expiry_date <= DATE_ADD(CURDATE(), INTERVAL 60 DAY)
        ORDER BY medicines.expiry_date ASC
        LIMIT 1
    """, (user_id,))
    expiring_medicine = cursor.fetchone()
    if expiring_medicine:
        add_notification(
            user_id,
            "Expiry Reminders",
            f"{expiring_medicine['name']} expires soon",
            f"Check your medicine stock. Expiry date: {expiring_medicine['expiry_date']}.",
            "/my_orders",
            f"expiry:{user_id}:{expiring_medicine['name']}:{expiring_medicine['expiry_date']}"
        )

    today_key = datetime.now().strftime("%Y-%m-%d")
    add_notification(
        user_id,
        "Health Tips Notifications",
        "Daily medicine safety tip",
        "Take medicines only as prescribed and confirm dose changes with a pharmacist or doctor.",
        "/ai_health_assistant",
        f"health-tip:{user_id}:{today_key}"
    )
    cursor.close()


def get_user_notifications(user_id, limit=None):
    sync_user_notifications(user_id)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    limit_sql = "LIMIT %s" if limit else ""
    params = [user_id]
    if limit:
        params.append(limit)
    cursor.execute(f"""
        SELECT *
        FROM notifications
        WHERE user_id=%s
        ORDER BY is_read ASC, created_at DESC, id DESC
        {limit_sql}
    """, tuple(params))
    notifications = cursor.fetchall()
    cursor.execute("""
        SELECT COUNT(*) AS unread
        FROM notifications
        WHERE user_id=%s AND is_read=0
    """, (user_id,))
    unread_count = (cursor.fetchone() or {}).get("unread", 0)
    cursor.close()
    return notifications, unread_count


def delivery_status_for_order_status(status):
    return {
        "Pending": "Order Received",
        "Approved": "Delivery Scheduled",
        "Packed": "Packed For Pickup",
        "Out For Delivery": "Out For Delivery",
        "Delivered": "Delivered",
        "Cancelled": "Delivery Cancelled",
        "Refunded": "Refunded",
    }.get(status, "Order Received")


def static_image_data_uri(relative_path):
    path = os.path.join(app.static_folder, relative_path)
    try:
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("ascii")
        extension = relative_path.rsplit(".", 1)[-1].lower()
        mime = "image/jpeg" if extension in ["jpg", "jpeg"] else "image/png"
        return f"data:{mime};base64,{encoded}"
    except OSError:
        return ""


def order_tracking_steps(status):
    current = status if status in ORDER_STATUS_STEPS else None
    current_index = ORDER_STATUS_STEPS.index(current) if current else -1
    return [
        {
            "name": step,
            "done": current_index >= index,
            "active": step == current,
        }
        for index, step in enumerate(ORDER_STATUS_STEPS)
    ]


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


def medicine_package_context(medicine):
    name = medicine.get("name") or "Medicine"
    category = normalize_category(medicine.get("category"))
    normalized = re.sub(r"[^a-z0-9]+", " ", f"{name} {category}".lower()).strip()
    price = medicine.get("price") or 0

    if any(word in normalized for word in ["tablet", "capsule"]):
        contents = "1 sealed strip containing 10 tablets/capsules"
        unit = "Strip pack"
        loose_note = "not for a loose single tablet/capsule"
        policy = "Loose single tablets/capsules are not sold separately online. Add quantity 1 to cart to order one strip pack; increase quantity for bulk strips."
    elif any(word in normalized for word in ["syrup", "suspension"]):
        contents = "1 sealed full bottle with outer carton when available"
        unit = "Full bottle pack"
        loose_note = "not for a loose partial bottle"
        policy = "Partial bottles are not sold separately online. Add quantity 1 to cart to order one sealed bottle pack; increase quantity for bulk bottles."
    elif "injection" in normalized or "iv fluid" in normalized:
        contents = "1 sealed full injection/vial pack as supplied by the manufacturer"
        unit = "Full injection pack"
        loose_note = "not for an opened or partial injection pack"
        policy = "Opened or partial injection packs are not sold online. Add quantity 1 to cart to order one sealed injection pack; increase quantity for bulk packs."
    elif any(word in normalized for word in ["cream", "gel", "ointment", "lotion", "solution"]):
        contents = "1 sealed full tube or bottle pack"
        unit = "Full topical pack"
        loose_note = "not for a loose or partially used tube/bottle"
        policy = "Loose or partially used tubes/bottles are not sold online. Add quantity 1 to cart to order one sealed topical pack; increase quantity for bulk packs."
    elif "drops" in normalized:
        contents = "1 sealed full drop bottle pack"
        unit = "Full drop pack"
        loose_note = "not for a loose or partially used drop bottle"
        policy = "Partial drop bottles are not sold online. Add quantity 1 to cart to order one sealed drop bottle; increase quantity for bulk packs."
    elif any(word in normalized for word in ["inhaler", "respules"]):
        contents = "1 sealed full inhaler/respule pack"
        unit = "Full respiratory pack"
        loose_note = "not for an opened or partial respiratory pack"
        policy = "Opened or partial inhaler/respule packs are not sold online. Add quantity 1 to cart to order one sealed respiratory pack; increase quantity for bulk packs."
    elif "sachet" in normalized or "powder" in normalized:
        contents = "1 sealed full sachet/box pack"
        unit = "Full sachet pack"
        loose_note = "not for a loose partial sachet or powder pack"
        policy = "Opened or partial sachet/powder packs are not sold online. Add quantity 1 to cart to order one sealed sachet pack; increase quantity for bulk packs."
    else:
        contents = "1 sealed full manufacturer pack"
        unit = "Full pack"
        loose_note = "not for an opened or partial pack"
        policy = "Opened or partial packs are not sold online. Add quantity 1 to cart to order one sealed pack; increase quantity for bulk packs."

    return {
        "selling_unit": unit,
        "contents": contents,
        "price_note": f"Listed price Rs. {price} is for 1 {unit.lower()}, {loose_note}.",
        "policy": policy
    }


def medicine_detail_context(medicine):
    name = medicine.get("name") or "Medicine"
    category = normalize_category(medicine.get("category"))
    department = normalize_category(medicine.get("department") or category)
    clean_name = re.sub(r"\s+", " ", name).strip()
    normalized_name = re.sub(r"[^a-z0-9]+", " ", clean_name.lower()).strip()
    strength_match = re.search(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|iu|%)\b", clean_name, re.I)
    strength = strength_match.group(0) if strength_match else ""
    generic_name = re.sub(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|iu|%)\b", "", clean_name, flags=re.I)
    generic_name = re.sub(r"\b(tablet|capsule|syrup|injection|cream|gel|ointment|drops|inhaler|solution|sachet)\b", "", generic_name, flags=re.I)
    generic_name = re.sub(r"\s+", " ", generic_name).strip(" -+/") or clean_name
    package = medicine_package_context(medicine)

    if "paracetamol" in normalized_name and "500" in normalized_name and "tablet" in normalized_name:
        return {
            "description": "Paracetamol 500mg Tablet is an analgesic and antipyretic medicine used for temporary relief of mild to moderate pain and fever. It should be taken only as directed on the label or by a healthcare professional.",
            "composition": "Paracetamol 500mg",
            "uses": "Used to reduce fever and relieve common pain such as headache, toothache, sore throat, muscle aches, joint pain, and cold or flu-related body pain.",
            "side_effects": "Paracetamol usually has few side effects when taken correctly. Rare but serious reactions can include allergy symptoms such as rash, itching, swelling, breathing difficulty, liver problems such as nausea or yellowing of the skin or eyes, and unusual bruising or bleeding. Taking too much can cause serious liver damage.",
            "dosage": "Store guidance for this product: take 1 tablet in the day and 1 tablet at night after food or as advised by a doctor. Do not take more than 2 tablets in 24 hours unless a doctor specifically tells you to. Avoid taking it with other medicines that also contain paracetamol.",
            "storage": "Keep tablets in their original container, tightly closed, at room temperature. Store away from excess heat, moisture, and direct sunlight, and keep out of sight and reach of children.",
            "brand_name": clean_name,
            "generic_alternative": "Paracetamol 500mg",
            "review_summary": "Customer reviews for this medicine are not available yet. You can still check stock status and add it to your cart if available.",
            "package": package
        }

    medicine_profiles = [
        {
            "keywords": ["antibiotic", "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "cefixime", "cefuroxime", "ceftriaxone", "metronidazole", "clindamycin", "levofloxacin"],
            "type": "antibiotic medicine",
            "uses": "Used for bacterial infections when prescribed by a doctor. It is not useful for viral illnesses such as common cold unless a clinician confirms a bacterial infection.",
            "side_effects": "May cause nausea, loose stools, stomach upset, headache, skin rash, allergy, or fungal overgrowth. Severe allergy, persistent diarrhea, breathing trouble, or swelling needs urgent medical help.",
            "dosage": "Take only in the dose, timing, and duration prescribed by a doctor. Complete the full course and do not stop early or reuse leftover antibiotics.",
            "storage": "Store in a cool, dry place away from sunlight. Keep the pack closed and keep all antibiotics out of reach of children."
        },
        {
            "keywords": ["diabetes", "metformin", "glimepiride", "gliclazide", "sitagliptin", "vildagliptin", "dapagliflozin", "empagliflozin", "pioglitazone", "insulin"],
            "type": "diabetes medicine",
            "uses": "Used to help manage blood sugar in diabetes as part of a treatment plan that may include diet, exercise, and monitoring.",
            "side_effects": "May cause low blood sugar, stomach upset, dizziness, sweating, weakness, increased urination, or weight changes depending on the medicine. Seek medical help for severe weakness, confusion, fainting, or very low sugar symptoms.",
            "dosage": "Use exactly as prescribed by your doctor. Do not skip meals or change the dose without medical advice, especially with insulin or sulfonylurea medicines.",
            "storage": "Store tablets in a cool, dry place. Insulin and some diabetes products may need refrigeration; follow the product label."
        },
        {
            "keywords": ["cardiac", "cardio", "heart", "amlodipine", "losartan", "telmisartan", "atenolol", "propranolol", "atorvastatin", "rosuvastatin", "clopidogrel", "warfarin", "digoxin"],
            "type": "heart and blood pressure medicine",
            "uses": "Used for conditions such as high blood pressure, cholesterol control, heart protection, rhythm problems, or blood clot prevention as prescribed.",
            "side_effects": "May cause dizziness, low blood pressure, swelling, tiredness, headache, muscle pain, slow pulse, or bleeding risk depending on the medicine. Unusual bleeding, chest pain, fainting, or severe muscle pain needs medical attention.",
            "dosage": "Take only as prescribed and at the same time each day when advised. Do not stop heart, blood pressure, cholesterol, or blood-thinning medicines suddenly without a doctor.",
            "storage": "Keep in the original pack at room temperature, away from heat and moisture."
        },
        {
            "keywords": ["gastric", "gi", "omeprazole", "pantoprazole", "rabeprazole", "esomeprazole", "ranitidine", "famotidine", "sucralfate", "domperidone", "ondansetron", "lactulose"],
            "type": "gastric medicine",
            "uses": "Used for acidity, reflux, stomach protection, nausea, vomiting, constipation, or other digestive symptoms based on the medicine type.",
            "side_effects": "May cause headache, constipation, diarrhea, dry mouth, stomach cramps, dizziness, or nausea. Severe abdominal pain, persistent vomiting, black stools, or allergic reactions need medical help.",
            "dosage": "Follow the doctor or label directions. Some acidity medicines work best before food, while nausea or constipation medicines have different timing.",
            "storage": "Store tightly closed in a cool, dry place. Keep liquids away from direct sunlight and check expiry before use."
        },
        {
            "keywords": ["cetirizine", "levocetirizine", "fexofenadine", "chlorpheniramine", "diphenhydramine", "desloratadine", "rupatadine", "hydroxyzine", "antihistamine", "allergy"],
            "type": "allergy medicine",
            "uses": "Used for allergy symptoms such as sneezing, runny nose, itching, watery eyes, skin allergy, or hives.",
            "side_effects": "May cause sleepiness, dry mouth, dizziness, headache, or tiredness. Avoid driving if the medicine makes you drowsy.",
            "dosage": "Take as directed on the label or by a doctor. Do not combine multiple allergy medicines unless advised.",
            "storage": "Store at room temperature in a dry place and keep away from children."
        },
        {
            "keywords": ["cough", "dextromethorphan", "ambroxol", "bromhexine", "guaifenesin", "salbutamol", "montelukast", "inhaler", "respiratory", "asthma"],
            "type": "cough and respiratory medicine",
            "uses": "Used for cough, chest congestion, wheezing, breathing support, or respiratory allergy symptoms depending on the medicine.",
            "side_effects": "May cause drowsiness, dry mouth, nausea, tremor, fast heartbeat, headache, or throat irritation. Breathing difficulty or worsening wheeze needs urgent care.",
            "dosage": "Use exactly as prescribed or as written on the label. Inhalers and respiratory medicines need correct technique and should not be overused.",
            "storage": "Keep bottles capped and inhalers at room temperature away from heat. Do not puncture or expose inhalers to high temperature."
        },
        {
            "keywords": ["vitamin", "supplement", "calcium", "zinc", "iron", "ors", "multivitamin", "biotin", "omega", "coenzyme", "glucosamine", "lycopene", "silymarin"],
            "type": "vitamin or supplement",
            "uses": "Used to support nutrition, hydration, mineral balance, bone health, immunity, or deficiency management depending on the product.",
            "side_effects": "May cause stomach upset, constipation, loose stools, nausea, or unusual taste. Excess intake can be harmful, especially with iron, fat-soluble vitamins, or minerals.",
            "dosage": "Take as advised on the label or by a healthcare professional. Do not exceed the recommended daily amount.",
            "storage": "Store sealed in a cool, dry place away from moisture and sunlight."
        },
        {
            "keywords": ["cream", "gel", "ointment", "lotion", "skin", "dermatology", "clotrimazole", "ketoconazole", "mupirocin", "adapalene", "tretinoin", "benzoyl", "permethrin", "hydrocortisone", "clobetasol"],
            "type": "skin or topical medicine",
            "uses": "Used on the skin for fungal infection, bacterial infection, inflammation, acne, itching, pain relief, or wound care depending on the product.",
            "side_effects": "May cause burning, redness, dryness, itching, peeling, or irritation at the application site. Stop and seek advice if severe irritation, swelling, or rash occurs.",
            "dosage": "Apply only to the affected area as prescribed or as directed on the label. Avoid eyes, mouth, and broken skin unless instructed.",
            "storage": "Keep the cap closed and store in a cool, dry place away from direct heat."
        },
        {
            "keywords": ["eye", "drops", "timolol", "ofloxacin eye", "moxifloxacin eye", "tobramycin eye", "latanoprost", "travoprost", "dorzolamide", "brimonidine"],
            "type": "eye medicine",
            "uses": "Used for eye infection, allergy, dryness, inflammation, or eye pressure control depending on the drop.",
            "side_effects": "May cause temporary burning, blurred vision, redness, watering, irritation, or bitter taste. Eye pain, vision changes, or swelling needs medical help.",
            "dosage": "Use only the number of drops and timing advised. Do not touch the dropper tip to the eye or any surface.",
            "storage": "Keep the bottle tightly closed. Store as per label and discard after the recommended period after opening."
        },
        {
            "keywords": ["injection", "iv fluid", "vial", "normal saline", "ringer lactate", "dextrose", "heparin", "enoxaparin"],
            "type": "injection or hospital-use medicine",
            "uses": "Used for hospital or clinician-administered treatment such as infection care, fluids, pain relief, blood thinning, or emergency support depending on the product.",
            "side_effects": "May cause injection-site pain, swelling, allergy, dizziness, bleeding risk, or medicine-specific reactions. Injections should be handled by trained staff.",
            "dosage": "Use only under medical supervision. Dose, route, dilution, and frequency must be decided by a qualified healthcare professional.",
            "storage": "Store according to the product label. Protect from heat and do not use if the seal is broken, cloudy, leaking, or expired."
        },
        {
            "keywords": ["psychiatric", "sleep", "sertraline", "fluoxetine", "escitalopram", "venlafaxine", "duloxetine", "amitriptyline", "olanzapine", "risperidone", "quetiapine", "diazepam", "clonazepam", "alprazolam", "zolpidem"],
            "type": "mental health or sleep medicine",
            "uses": "Used for conditions such as depression, anxiety, sleep problems, mood symptoms, or psychiatric care when prescribed.",
            "side_effects": "May cause sleepiness, dizziness, dry mouth, weight changes, mood changes, nausea, or dependence risk for some medicines. Worsening mood, confusion, breathing difficulty, or severe drowsiness needs urgent advice.",
            "dosage": "Take exactly as prescribed. Do not stop suddenly or change the dose without a doctor, as withdrawal or symptom worsening can occur.",
            "storage": "Store securely at room temperature, away from children and anyone for whom it was not prescribed."
        },
        {
            "keywords": ["antiviral", "tenofovir", "lamivudine", "zidovudine", "efavirenz", "dolutegravir", "remdesivir", "acyclovir", "valacyclovir", "oseltamivir"],
            "type": "antiviral medicine",
            "uses": "Used for viral infections or long-term viral disease management when prescribed by a doctor.",
            "side_effects": "May cause nausea, headache, tiredness, stomach upset, dizziness, or liver/kidney-related effects depending on the medicine.",
            "dosage": "Take exactly as prescribed and do not miss doses, especially for long-term antiviral treatment.",
            "storage": "Store in the original container in a cool, dry place unless the label says otherwise."
        },
        {
            "keywords": ["pain", "analgesic", "ibuprofen", "diclofenac", "naproxen", "aceclofenac", "ketorolac", "meloxicam", "piroxicam", "celecoxib", "etoricoxib", "aspirin"],
            "type": "pain relief medicine",
            "uses": "Used for pain, swelling, inflammation, fever, or body aches depending on the medicine.",
            "side_effects": "May cause acidity, stomach pain, nausea, dizziness, swelling, kidney strain, or bleeding risk. Avoid self-use if you have ulcers, kidney disease, blood thinner use, or pregnancy unless advised.",
            "dosage": "Take only as directed by a doctor or label. Use the lowest effective dose for the shortest time and avoid combining similar painkillers.",
            "storage": "Store in a cool, dry place away from moisture and sunlight."
        }
    ]

    profile = next(
        (item for item in medicine_profiles if any(keyword in normalized_name or keyword in category.lower() or keyword in department.lower() for keyword in item["keywords"])),
        None
    )

    if profile:
        return {
            "description": f"{clean_name} is a {profile['type']} available at Yuvraj Medical. Use it only for the condition and duration advised by a qualified healthcare professional.",
            "composition": f"{generic_name}{' ' + strength if strength else ''}".strip(),
            "uses": profile["uses"],
            "side_effects": profile["side_effects"],
            "dosage": profile["dosage"],
            "storage": profile["storage"],
            "brand_name": clean_name,
            "generic_alternative": generic_name,
            "review_summary": "Customer reviews for this medicine are not available yet. You can still check stock status and full-pack availability before ordering.",
            "package": package
        }

    return {
        "description": f"{clean_name} is listed in the {category} category at Yuvraj Medical. Check suitability with a qualified healthcare professional before use.",
        "composition": f"{generic_name}{' ' + strength if strength else ''}".strip(),
        "uses": f"Commonly requested for {department.lower()} care based on its catalog classification. Use only as advised by a doctor or pharmacist.",
        "side_effects": "Side effects can vary by patient and medicine. Stop use and contact a doctor if you notice allergy, severe discomfort, or unusual symptoms.",
        "dosage": "Follow the dosage written on your prescription or product label. Do not change dose or frequency without medical advice.",
        "storage": "Store in a cool, dry place away from direct sunlight and keep out of reach of children.",
        "brand_name": clean_name,
        "generic_alternative": generic_name,
        "review_summary": "Customers can order this medicine through the catalog. Detailed product reviews are not available yet.",
        "package": package
    }


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


AI_FEATURE_CONFIG = {
    "medicine_search": {"title": "AI Medicine Search"},
    "symptom_checker": {"title": "AI Symptom Checker"},
    "health_assistant": {"title": "AI Health Assistant"},
    "disease_info": {"title": "AI Disease Information"},
    "medicine_suggestions": {"title": "AI Medicine Suggestions"},
    "reminder_suggestions": {"title": "AI Medicine Reminder Suggestions"},
    "health_question": {
        "title": "AI Health Assistant",
    },
    "general": {"title": "AI Health Assistant"},
}


SYMPTOM_GUIDANCE = {
    "fever": {
        "category": "Fever and pain relief",
        "steps": "Check temperature, drink fluids, rest, and avoid self-medicating with antibiotics.",
        "red_flags": "Very high fever, fever longer than 3 days, stiff neck, confusion, breathlessness, rash, dehydration, infants, pregnancy, or serious chronic illness.",
    },
    "cough": {
        "category": "Cough, cold, and respiratory care",
        "steps": "Warm fluids, steam comfort, avoid smoke/dust, and choose cough support based on dry cough or phlegm.",
        "red_flags": "Breathing trouble, chest pain, blood in cough, wheezing, blue lips, fever more than 3 days, or symptoms lasting more than 2 weeks.",
    },
    "cold": {
        "category": "Cold, allergy, and congestion care",
        "steps": "Rest, fluids, saline gargle or steam comfort, and avoid sharing towels/utensils.",
        "red_flags": "Severe headache, chest pain, breathing difficulty, persistent high fever, or symptoms worsening after improvement.",
    },
    "acidity": {
        "category": "Gastric and acidity care",
        "steps": "Eat smaller meals, avoid spicy/oily foods, avoid lying down after food, and track trigger foods.",
        "red_flags": "Chest pressure, vomiting blood, black stool, severe abdominal pain, weight loss, or repeated vomiting.",
    },
    "pain": {
        "category": "Pain relief and anti-inflammatory care",
        "steps": "Rest the affected area, use gentle heat/cold as suitable, and avoid repeated painkiller use without advice.",
        "red_flags": "Severe injury, swelling, weakness, numbness, chest pain, severe headache, or pain with fever.",
    },
    "allergy": {
        "category": "Allergy and antihistamine care",
        "steps": "Avoid the trigger, wash exposed skin, and monitor rash/itching/sneezing patterns.",
        "red_flags": "Face/lip swelling, breathing difficulty, wheezing, dizziness, or fast-spreading rash.",
    },
    "skin": {
        "category": "Skin care, antifungal, antibacterial, or anti-itch care",
        "steps": "Keep the area clean and dry, avoid scratching, and avoid mixing creams without advice.",
        "red_flags": "Pus, fever, spreading redness, severe pain, diabetes, eye/genital area involvement, or no improvement.",
    },
    "diabetes": {
        "category": "Diabetes care",
        "steps": "Monitor sugar, keep meals regular, stay hydrated, and take medicines exactly as prescribed.",
        "red_flags": "Very low sugar symptoms, confusion, fainting, vomiting, very high readings, or infection wounds.",
    },
    "blood pressure": {
        "category": "Heart and blood pressure care",
        "steps": "Check readings correctly, reduce salt, avoid missed doses, and keep follow-up with your doctor.",
        "red_flags": "Chest pain, severe headache, weakness on one side, breathlessness, fainting, or very high readings.",
    },
}


DISEASE_GUIDANCE = {
    "diabetes": "Diabetes means blood sugar stays higher than normal. Common care includes regular monitoring, diet planning, exercise, foot care, and doctor-prescribed medicines. Watch for very low sugar, wounds, infection, vomiting, or confusion.",
    "hypertension": "Hypertension means blood pressure stays high. Care includes regular BP checks, low-salt food, exercise, stress control, and taking prescribed medicines consistently. Emergency signs include chest pain, severe headache, weakness, or breathlessness.",
    "asthma": "Asthma causes airway narrowing with wheezing, cough, chest tightness, or breathlessness. Avoid triggers, follow inhaler plans, and seek urgent help for severe breathing difficulty or blue lips.",
    "acidity": "Acidity or reflux can cause burning, sour burps, bloating, or throat irritation. Smaller meals and avoiding trigger foods helps. Chest pressure, black stool, blood vomiting, or severe pain needs urgent care.",
    "skin infection": "Skin infections can cause redness, itching, swelling, pus, or pain. Keep the area clean and avoid sharing towels. Fever, spreading redness, diabetes, or pus needs medical review.",
}


URGENT_TERMS = {
    "chest pain", "breathing difficulty", "shortness of breath", "fainting",
    "stroke", "severe bleeding", "blood vomiting", "suicide", "overdose",
    "blue lips", "unconscious", "seizure"
}


SYMPTOM_ALIASES = {
    "fever": ("fever", "temperature", "body hot", "body heat", "getting hot", "very hot", "hot body", "chills"),
    "cough": ("cough", "coughing", "khansi"),
    "cold": ("cold", "runny nose", "blocked nose", "sneezing", "throat pain", "sore throat"),
    "acidity": ("acidity", "acid", "gas", "gastric", "heartburn", "burning stomach", "reflux"),
    "pain": ("pain", "ache", "headache", "body pain", "back pain", "joint pain"),
    "allergy": ("allergy", "itching", "rash", "hives", "sneezing allergy"),
    "skin": ("skin", "pimple", "fungal", "redness", "itchy skin"),
    "diabetes": ("diabetes", "sugar", "blood sugar"),
    "blood pressure": ("bp", "blood pressure", "hypertension"),
}


DIET_TERMS = ("diet", "nutrition", "food plan", "meal plan", "weight loss", "weight gain", "protein")


def ai_terms(query):
    terms = [
        term
        for term in re.findall(r"[A-Za-z0-9]+", query or "")
        if len(term) >= 3
    ][:8]
    return terms


def fetch_ai_medicine_matches(query, limit=8):
    terms = ai_terms(query)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if terms:
        where_parts = []
        params = []
        for term in terms:
            like = f"%{term}%"
            where_parts.append("(name LIKE %s OR category LIKE %s OR department LIKE %s)")
            params.extend([like, like, like])

        cursor.execute(f"""
            SELECT id, name, category, department, price, stock, prescription_required
            FROM medicines
            WHERE {" OR ".join(where_parts)}
            ORDER BY name ASC
            LIMIT %s
        """, tuple(params + [limit]))
    else:
        cursor.execute("""
            SELECT id, name, category, department, price, stock, prescription_required
            FROM medicines
            ORDER BY stock DESC, name ASC
            LIMIT %s
        """, (limit,))

    rows = cursor.fetchall()
    cursor.close()
    return rows


def format_medicine_matches(rows):
    if not rows:
        return "No matching medicines were found in the local inventory."

    lines = []
    for row in rows[:5]:
        rx_note = "Prescription required" if row.get("prescription_required") else "Direct purchase may be available"
        stock_note = f"{row.get('stock') or 0} packs in stock"
        lines.append(
            f"- {row.get('name')} | Rs. {row.get('price')} | {stock_note} | {rx_note}"
        )
    return "\n".join(lines)


def symptom_profile(user_text):
    text = (user_text or "").lower()
    for key, aliases in SYMPTOM_ALIASES.items():
        if any(alias in text for alias in aliases):
            return key, SYMPTOM_GUIDANCE[key]
    return None, {
        "category": "General health support",
        "steps": "Note when symptoms started, severity, temperature if fever is present, current medicines, allergies, and any known illness.",
        "red_flags": "Severe pain, breathing difficulty, chest pain, fainting, confusion, dehydration, pregnancy, infant age, or symptoms getting worse.",
    }


def disease_profile(user_text):
    text = (user_text or "").lower()
    for key, description in DISEASE_GUIDANCE.items():
        if key in text:
            return key.title(), description
    return "General Disease Information", (
        "Please enter a disease name such as diabetes, hypertension, asthma, acidity, or skin infection. "
        "I can explain common symptoms, basic care, prevention, and warning signs."
    )


def reminder_suggestion(user_text):
    clean_text = user_text.strip()
    times = re.findall(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", clean_text, flags=re.I)
    schedule = "\n".join(f"- Reminder at {time.strip()}: take only the dose written on your prescription/label." for time in times[:6])
    if not schedule:
        schedule = (
            "- Morning: after breakfast if your prescription says morning dose.\n"
            "- Afternoon: after lunch if your prescription says afternoon dose.\n"
            "- Night: after dinner or before sleep only if your prescription says night dose."
        )

    return (
        "Medicine Reminder Plan\n"
        f"{schedule}\n\n"
        "Tips:\n"
        "- Do not change dose or timing without doctor/pharmacist advice.\n"
        "- Keep a 10 minute early alert.\n"
        "- Mark the dose as taken only after taking it."
    )


def symptom_answer(user_text, heading="AI Symptom Checker"):
    symptom_key, profile = symptom_profile(user_text)
    symptom_note = symptom_key.title() if symptom_key else "General symptom"
    common_signs = {
        "fever": "Hot body\n- Chills\n- Weakness or body pain",
        "cough": "Coughing\n- Throat irritation\n- Chest congestion or dry cough",
        "cold": "Runny nose\n- Sneezing\n- Mild fever or throat irritation",
        "acidity": "Burning in stomach/chest\n- Sour burps\n- Bloating",
        "pain": "Pain or ache\n- Tiredness\n- Tenderness in the affected area",
        "allergy": "Sneezing or itching\n- Rash\n- Watery eyes",
        "skin": "Redness or itching\n- Rash\n- Swelling or irritation",
        "diabetes": "High/low sugar symptoms\n- Excess thirst\n- Frequent urination",
        "blood pressure": "Headache or dizziness\n- Chest discomfort\n- Unusual tiredness",
    }.get(symptom_key, "New or unclear symptom\n- Note start time\n- Note severity")

    return (
        f"{symptom_note}\n\n"
        "Common signs:\n"
        f"- {common_signs}\n\n"
        "Suggestions:\n"
        f"- {profile['steps']}\n"
        "- Drink enough water and rest.\n"
        "- Use only prescribed or pharmacist-confirmed medicine.\n\n"
        "See a doctor if:\n"
        f"- {profile['red_flags']}"
    )


def nutrition_answer(user_text):
    text = user_text.lower()
    goal = "general wellness"
    if "weight loss" in text or "lose" in text:
        goal = "weight loss"
    elif "weight gain" in text or "gain" in text:
        goal = "weight gain"
    elif "diabetes" in text or "sugar" in text:
        goal = "diabetes-friendly eating"
    elif "protein" in text:
        goal = "higher protein meals"

    extra = {
        "weight loss": "- Keep portions controlled, prefer dal/eggs/paneer/curd with vegetables, and reduce sugary drinks and fried snacks.",
        "weight gain": "- Add calorie-dense healthy foods like milk, curd, paneer, nuts, peanut butter, eggs, and frequent small meals.",
        "diabetes-friendly eating": "- Prefer high-fiber meals, avoid sugary drinks, keep rice/roti portions steady, and monitor sugar as advised.",
        "higher protein meals": "- Include dal, sprouts, eggs, paneer, curd, chicken/fish if non-vegetarian, or soy/tofu.",
        "general wellness": "- Use balanced meals: half plate vegetables/salad, one quarter protein, one quarter roti/rice/poha/upma, plus water.",
    }[goal]

    return (
        f"Nutrition Plan: {goal.title()}\n\n"
        "Daily structure:\n"
        "- Breakfast: protein + fruit or light carbs.\n"
        "- Lunch: roti/rice + dal/paneer/egg/chicken + vegetables.\n"
        "- Snack: fruit, nuts, roasted chana, or buttermilk.\n"
        "- Dinner: lighter protein + vegetables.\n"
        f"{extra}\n\n"
        "Ask a dietitian/doctor for a personal plan if you have diabetes, kidney/liver disease, pregnancy, major weight change, or long-term illness."
    )


def manual_ai_answer(feature, user_text):
    feature = feature if feature in AI_FEATURE_CONFIG else "health_assistant"
    text = (user_text or "").strip()
    lower_text = text.lower()
    symptom_key, profile = symptom_profile(text)

    if any(term in lower_text for term in URGENT_TERMS):
        return (
            "Urgent Warning\n"
            "Your message includes symptoms that can be serious. Please seek urgent medical care now or contact local emergency services.\n\n"
            "While waiting, avoid self-medicating unless a doctor has already instructed you."
        )

    if feature == "medicine_search":
        matches = fetch_ai_medicine_matches(text, limit=5)
        return (
            f"Medicine Search: {text}\n\n"
            "Found in Yuvraj Medical:\n"
            f"{format_medicine_matches(matches)}\n\n"
            "Confirm suitability, dose, allergy, pregnancy safety, and prescription need with staff or a doctor."
        )

    if feature == "medicine_suggestions":
        matches = fetch_ai_medicine_matches(f"{profile['category']} {text}", limit=5)
        return (
            "Medicine Suggestions\n\n"
            f"Care category: {profile['category']}\n\n"
            "Ask staff/pharmacist about:\n"
            f"{format_medicine_matches(matches)}\n\n"
            "These are catalog suggestions, not a prescription."
        )

    if feature == "symptom_checker":
        return symptom_answer(text)

    if feature == "disease_info":
        if symptom_key and not any(disease in lower_text for disease in DISEASE_GUIDANCE):
            return symptom_answer(text, heading="AI Disease Information")

        disease_name, description = disease_profile(text)
        return (
            f"{disease_name}\n\n"
            f"{description}\n\n"
            "Care basics:\n"
            "- Take prescribed medicines on time.\n"
            "- Track symptoms and triggers.\n"
            "- Keep follow-up appointments.\n\n"
            "See a doctor if symptoms worsen or become severe."
        )

    if feature == "reminder_suggestions":
        return reminder_suggestion(text)

    if any(term in lower_text for term in DIET_TERMS):
        return nutrition_answer(text)

    if symptom_key:
        return symptom_answer(text, heading="AI Health Assistant")

    if any(disease in lower_text for disease in DISEASE_GUIDANCE):
        disease_name, description = disease_profile(text)
        return (
            f"{disease_name}\n\n"
            f"{description}\n\n"
            "Care basics:\n"
            "- Follow your doctor's plan.\n"
            "- Track symptoms and triggers.\n"
            "- Keep follow-up appointments.\n\n"
            "Seek urgent care if symptoms become severe."
        )

    return (
        "What can I help with?\n\n"
        "- Find medicine\n"
        "- Check symptoms\n"
        "- Medicine info\n"
        "- Medicine reminders\n"
        "- Disease information\n\n"
        "Try: fever, cold, headache, diabetes, Paracetamol, or remind me at 9am."
    )


def fetch_ai_medicine_context(query):
    rows = fetch_ai_medicine_matches(query, limit=30)
    if not rows:
        return "No matching local store medicines were found for this query."
    return format_medicine_matches(rows)


def call_ai_health_assistant(feature, user_text, medicine_context=None):
    return manual_ai_answer(feature, user_text)


@app.route("/ai_health_assistant")
def ai_health_assistant():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    user_id = session["user"]["id"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicine_id, quantity
        FROM cart
        WHERE user_id=%s
    """, (user_id,))
    cart_rows = cursor.fetchall()
    cursor.close()

    cart_count = sum(row["quantity"] for row in cart_rows)
    return render_template("ai_health_assistant.html", cart_count=cart_count)


@app.route("/ai_health_assistant/ask", methods=["POST"])
def ai_health_assistant_ask():
    if "user" not in session:
        return jsonify({"error": "Please login to use AI Health Assistant."}), 401

    data = request.get_json(silent=True) or {}
    feature = (data.get("feature") or "general").strip()
    user_text = (data.get("message") or "").strip()

    if feature not in AI_FEATURE_CONFIG:
        return jsonify({"error": "Invalid AI feature selected."}), 400

    if len(user_text) < 2:
        return jsonify({"error": "Please enter your question."}), 400

    if len(user_text) > 1200:
        return jsonify({"error": "Please keep your question under 1200 characters."}), 400

    answer = call_ai_health_assistant(feature, user_text)
    return jsonify({
        "answer": answer,
        "feature": AI_FEATURE_CONFIG[feature]["title"],
        "safety_note": "Manual guidance only. Please confirm treatment, dose, and prescription needs with a qualified doctor or pharmacist.",
    })


@app.route("/medicine/<int:id>")
def medicine_details(id):
    if "user" not in session:
        return redirect("/login")

    ensure_reviews_feedback_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    medicine = cursor.fetchone()
    cursor.close()

    if not medicine:
        flash("Medicine not found.")
        return redirect("/")

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM medicines
        WHERE id <> %s
          AND (
                COALESCE(category, '') = COALESCE(%s, '')
             OR COALESCE(department, '') = COALESCE(%s, '')
          )
        ORDER BY stock DESC, name ASC
        LIMIT 6
    """, (id, medicine.get("category"), medicine.get("department")))
    related_medicines = cursor.fetchall()
    cursor.close()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicine_id, quantity
        FROM cart
        WHERE user_id=%s
    """, (session["user"]["id"],))
    cart_rows = cursor.fetchall()
    cursor.close()

    cart = {str(r["medicine_id"]): r["quantity"] for r in cart_rows}

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(*) AS review_count,
               COALESCE(AVG(rating), 0) AS average_rating
        FROM reviews_feedback
        WHERE medicine_id=%s
          AND review_type='Medicine Rating'
          AND rating IS NOT NULL
    """, (id,))
    review_summary = cursor.fetchone() or {"review_count": 0, "average_rating": 0}
    cursor.execute("""
        SELECT reviews_feedback.*, users.name AS customer_name
        FROM reviews_feedback
        LEFT JOIN users ON users.id = reviews_feedback.user_id
        WHERE reviews_feedback.medicine_id=%s
          AND reviews_feedback.review_type='Medicine Rating'
        ORDER BY reviews_feedback.id DESC
        LIMIT 4
    """, (id,))
    medicine_reviews = cursor.fetchall()
    cursor.close()

    return render_template(
        "medicine_details.html",
        medicine=medicine,
        details=medicine_detail_context(medicine),
        related_medicines=related_medicines,
        cart=cart,
        cart_count=sum(cart.values()),
        review_summary=review_summary,
        medicine_reviews=medicine_reviews,
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
        referral_code = request.form.get("referral_code", "").strip().upper()
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
            "referral_code": referral_code,
        }
        action = request.form.get("action", "create_account")
        db = get_db()

        try:
            ensure_referral_schema()
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

            inviter = None
            if referral_code:
                inviter = find_user_by_referral_code(referral_code)
                if not inviter:
                    return render_template(
                        "register.html",
                        error="Invalid referral code. Please check it or leave the field blank.",
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
                new_user_id = cursor.lastrowid
                if inviter and inviter["id"] != new_user_id:
                    cursor.execute("""
                        INSERT IGNORE INTO referral_rewards (
                            inviter_user_id,
                            invitee_user_id,
                            referral_code,
                            reward_amount,
                            status,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        inviter["id"],
                        new_user_id,
                        referral_code,
                        100,
                        "Expected",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    referral_code = request.args.get("ref", "").strip().upper()
    form = {"referral_code": referral_code, "country_code": "+91", "role": "customer"} if referral_code else None
    return render_template("register.html", form=form)
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
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "ok": False,
                "redirect": "/upload_prescription",
                "message": f"{medicine['name']} requires prescription."
            }), 403
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
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "message": f"Cart Error: {e}"}), 500
        return f"Cart Error: {e}"

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT quantity FROM cart WHERE user_id=%s AND medicine_id=%s",
            (user_id, id)
        )
        row = cursor.fetchone() or {"quantity": 0}
        cursor.execute("SELECT COALESCE(SUM(quantity),0) AS count FROM cart WHERE user_id=%s", (user_id,))
        count_row = cursor.fetchone() or {"count": 0}
        cursor.close()
        return jsonify({"ok": True, "quantity": row["quantity"], "cart_count": count_row["count"]})

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
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "ok": False,
                "redirect": "/upload_prescription",
                "message": f"{medicine['name']} requires prescription."
            }), 403
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
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT quantity FROM cart WHERE user_id=%s AND medicine_id=%s",
            (user_id, id)
        )
        row = cursor.fetchone() or {"quantity": 0}
        cursor.execute("SELECT COALESCE(SUM(quantity),0) AS count FROM cart WHERE user_id=%s", (user_id,))
        count_row = cursor.fetchone() or {"count": 0}
        cursor.close()
        return jsonify({"ok": True, "quantity": row["quantity"], "cart_count": count_row["count"]})
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
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT quantity FROM cart WHERE user_id=%s AND medicine_id=%s",
            (user_id, id)
        )
        row = cursor.fetchone() or {"quantity": 0}
        cursor.execute("SELECT COALESCE(SUM(quantity),0) AS count FROM cart WHERE user_id=%s", (user_id,))
        count_row = cursor.fetchone() or {"count": 0}
        cursor.close()
        return jsonify({"ok": True, "quantity": row["quantity"], "cart_count": count_row["count"]})
    return redirect(request.referrer or "/")


def ensure_cart_feature_schema():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_saved_later (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            medicine_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_saved_item (user_id, medicine_id),
            INDEX idx_saved_user (user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            medicine_id INT NOT NULL,
            notify_when_available TINYINT(1) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_wishlist_item (user_id, medicine_id),
            INDEX idx_wishlist_user (user_id)
        )
    """)
    try:
        cursor.execute("""
            ALTER TABLE wishlist
            ADD COLUMN notify_when_available TINYINT(1) NOT NULL DEFAULT 0
        """)
    except Exception:
        pass
    db.commit()
    cursor.close()


CART_COUPONS = {
    "SAVE10": {
        "type": "percent",
        "value": 10,
        "min_subtotal": 100,
        "label": "10% off on cart value above Rs. 100"
    },
    "HEALTH50": {
        "type": "flat",
        "value": 50,
        "min_subtotal": 500,
        "label": "Rs. 50 off on cart value above Rs. 500"
    },
    "FREESHIP": {
        "type": "free_delivery",
        "value": 0,
        "min_subtotal": 200,
        "label": "Free delivery above Rs. 200"
    }
}


REWARD_COUPON_COSTS = {
    "FREESHIP": 120,
    "SAVE10": 250,
    "HEALTH50": 500,
}


def calculate_cart_totals(subtotal):
    coupon_code = session.get("cart_coupon")
    coupon = CART_COUPONS.get(coupon_code)
    delivery_charge = 0 if subtotal == 0 or subtotal >= 500 else 40
    discount = 0
    coupon_message = None

    if coupon:
        if subtotal >= coupon["min_subtotal"]:
            if coupon["type"] == "percent":
                discount = round(subtotal * coupon["value"] / 100, 2)
            elif coupon["type"] == "flat":
                discount = min(coupon["value"], subtotal)
            elif coupon["type"] == "free_delivery":
                delivery_charge = 0
            coupon_message = coupon["label"]
        else:
            coupon_message = f"{coupon_code} applies above Rs. {coupon['min_subtotal']}."

    payable_total = max(subtotal - discount, 0) + delivery_charge
    return {
        "subtotal": subtotal,
        "discount": discount,
        "delivery_charge": delivery_charge,
        "payable_total": payable_total,
        "coupon_code": coupon_code if coupon else None,
        "coupon_message": coupon_message,
        "estimated_delivery": "1-2 business days"
    }


def rupees_value(value):
    return float(value or 0)


def ensure_referral_schema():
    if app.config.get("REFERRAL_SCHEMA_READY"):
        return

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inviter_user_id INT NOT NULL,
            invitee_user_id INT NOT NULL,
            referral_code VARCHAR(40) NOT NULL,
            reward_amount DECIMAL(10,2) NOT NULL DEFAULT 100,
            status VARCHAR(40) NOT NULL DEFAULT 'Expected',
            created_at DATETIME NOT NULL,
            UNIQUE KEY uniq_referral_invitee (invitee_user_id),
            INDEX idx_referral_inviter (inviter_user_id),
            INDEX idx_referral_code (referral_code)
        )
    """)
    db.commit()
    cursor.close()
    app.config["REFERRAL_SCHEMA_READY"] = True


def referral_code_for_user(user):
    referral_name = re.sub(r"[^A-Z0-9]", "", (user.get("name") or "YUVRAJ").upper())[:4] or "YMR"
    return f"{referral_name}{int(user['id']):04d}"


def find_user_by_referral_code(code):
    code = (code or "").strip().upper()
    if not code:
        return None

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM users WHERE role='customer'")
    users = cursor.fetchall()
    cursor.close()

    for user in users:
        if referral_code_for_user(user) == code:
            return user
    return None


def reward_tier_for_points(points):
    tiers = [
        {"name": "Wellness Starter", "min": 0, "next": 750, "accent": "Fresh savings unlocked"},
        {"name": "Care Plus", "min": 750, "next": 1800, "accent": "Bigger monthly rewards"},
        {"name": "Gold Health Circle", "min": 1800, "next": 3600, "accent": "Priority coupons and cashback"},
        {"name": "Platinum Care", "min": 3600, "next": None, "accent": "Top tier medicine benefits"},
    ]
    active = tiers[0]
    for tier in tiers:
        if points >= tier["min"]:
            active = tier
    next_points = active["next"]
    progress = 100 if next_points is None else min(100, int((points - active["min"]) * 100 / (next_points - active["min"])))
    return active, progress, next_points


def build_rewards_context(user_id):
    ensure_payment_schema()
    ensure_referral_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone() or {"id": user_id, "name": "Customer", "email": ""}

    cursor.execute("""
        SELECT id, total, status, date, payment_status
        FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
    """, (user_id,))
    orders = cursor.fetchall()

    cursor.execute("""
        SELECT payments.*, orders.status AS order_status
        FROM payments
        JOIN orders ON orders.id = payments.order_id
        WHERE payments.user_id=%s
        ORDER BY payments.id DESC
        LIMIT 10
    """, (user_id,))
    payments = cursor.fetchall()

    cursor.execute("""
        SELECT referral_rewards.*,
               users.name AS invitee_name,
               users.email AS invitee_email
        FROM referral_rewards
        LEFT JOIN users ON users.id = referral_rewards.invitee_user_id
        WHERE referral_rewards.inviter_user_id=%s
        ORDER BY referral_rewards.id DESC
    """, (user_id,))
    referral_rewards = cursor.fetchall()
    cursor.close()

    completed_orders = [order for order in orders if order.get("status") == "Delivered"]
    active_orders = [order for order in orders if order.get("status") in ["Pending", "Approved", "Packed", "Out For Delivery"]]
    total_spent = sum(rupees_value(order.get("total")) for order in orders if order.get("status") != "Cancelled")
    delivered_spent = sum(rupees_value(order.get("total")) for order in completed_orders)
    points = int(total_spent // 10) + len(completed_orders) * 50
    pending_points = int(sum(rupees_value(order.get("total")) for order in active_orders) // 10)
    cashback_available = round(sum(rupees_value(payment.get("amount")) * 0.02 for payment in payments if payment.get("status") == "Verified"), 2)
    cashback_pending = round(sum(rupees_value(payment.get("amount")) * 0.02 for payment in payments if payment.get("status") in ["Pending Verification", "Pending COD"]), 2)
    tier, tier_progress, next_tier_points = reward_tier_for_points(points)

    referral_code = referral_code_for_user(user)
    host = request.host_url.rstrip("/")
    referral_link = f"{host}/register?ref={referral_code}"
    whatsapp_message = (
        "Hi, I use Yuvraj Medical for online medicine orders. "
        f"Use my referral code {referral_code} and register here: {referral_link}"
    )
    whatsapp_share_url = f"https://wa.me/?text={quote(whatsapp_message)}"
    referral_completed = len([item for item in referral_rewards if item.get("status") in ["Rewarded", "Credited"]])
    referral_pending = len([item for item in referral_rewards if item.get("status") == "Expected"])
    referral_bonus = sum(rupees_value(item.get("reward_amount")) for item in referral_rewards)

    coupons = []
    for code, coupon in CART_COUPONS.items():
        point_cost = REWARD_COUPON_COSTS.get(code, 0)
        coupons.append({
            "code": code,
            "label": coupon["label"],
            "min_subtotal": coupon["min_subtotal"],
            "point_cost": point_cost,
            "available": points >= point_cost,
        })

    cashback_history = []
    for payment in payments:
        amount = rupees_value(payment.get("amount"))
        cashback_history.append({
            "order_id": payment.get("order_id"),
            "method": payment.get("method"),
            "amount": amount,
            "cashback": round(amount * 0.02, 2),
            "status": "Credited" if payment.get("status") == "Verified" else "Pending",
            "created_at": payment.get("created_at"),
        })

    point_history = []
    for order in orders[:8]:
        base_points = int(rupees_value(order.get("total")) // 10)
        bonus = 50 if order.get("status") == "Delivered" else 0
        point_history.append({
            "order_id": order.get("id"),
            "status": order.get("status"),
            "points": base_points + bonus,
            "date": order.get("date"),
        })

    return {
        "user": user,
        "summary": {
            "points": points,
            "pending_points": pending_points,
            "cashback_available": cashback_available,
            "cashback_pending": cashback_pending,
            "orders": len(orders),
            "delivered_orders": len(completed_orders),
            "total_spent": total_spent,
            "delivered_spent": delivered_spent,
        },
        "tier": tier,
        "tier_progress": tier_progress,
        "next_tier_points": next_tier_points,
        "referral": {
            "code": referral_code,
            "link": referral_link,
            "whatsapp_url": whatsapp_share_url,
            "completed": referral_completed,
            "pending": referral_pending,
            "bonus": referral_bonus,
            "max_bonus": 100,
            "expected_reward": sum(rupees_value(item.get("reward_amount")) for item in referral_rewards if item.get("status") == "Expected"),
            "history": referral_rewards,
        },
        "coupons": coupons,
        "cashback_history": cashback_history,
        "point_history": point_history,
    }


@app.route("/rewards")
def rewards():
    if "user" not in session:
        return redirect("/login")

    return render_template("rewards.html", **build_rewards_context(session["user"]["id"]))


@app.route("/rewards/redeem", methods=["POST"])
def redeem_reward():
    if "user" not in session:
        return redirect("/login")

    code = (request.form.get("coupon_code") or "").strip().upper()
    rewards_context = build_rewards_context(session["user"]["id"])
    available_codes = {
        coupon["code"] for coupon in rewards_context["coupons"] if coupon["available"]
    }
    if code in available_codes:
        session["cart_coupon"] = code
        flash(f"Reward coupon {code} is ready in your cart.")
        return redirect("/cart")

    flash("This reward coupon needs more loyalty points.")
    return redirect("/rewards")


@app.route("/cart/remove/<int:id>")
def remove_from_cart(id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM cart WHERE user_id=%s AND medicine_id=%s",
        (session["user"]["id"], id)
    )
    db.commit()
    cursor.close()
    return redirect("/cart")


@app.route("/cart/save_for_later/<int:id>")
def save_for_later(id):
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
    db = get_db()
    user_id = session["user"]["id"]
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT quantity FROM cart WHERE user_id=%s AND medicine_id=%s",
        (user_id, id)
    )
    item = cursor.fetchone()
    if item:
        cursor.execute("""
            INSERT INTO cart_saved_later (user_id, medicine_id, quantity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        """, (user_id, id, item["quantity"]))
        cursor.execute(
            "DELETE FROM cart WHERE user_id=%s AND medicine_id=%s",
            (user_id, id)
        )
        db.commit()
    cursor.close()
    return redirect("/cart")


@app.route("/cart/move_saved_to_cart/<int:id>")
def move_saved_to_cart(id):
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
    db = get_db()
    user_id = session["user"]["id"]
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT quantity FROM cart_saved_later WHERE user_id=%s AND medicine_id=%s",
        (user_id, id)
    )
    item = cursor.fetchone()
    if item:
        cursor.execute("""
            INSERT INTO cart (user_id, medicine_id, quantity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        """, (user_id, id, item["quantity"]))
        cursor.execute(
            "DELETE FROM cart_saved_later WHERE user_id=%s AND medicine_id=%s",
            (user_id, id)
        )
        db.commit()
    cursor.close()
    return redirect("/cart")


@app.route("/cart/remove_saved/<int:id>")
def remove_saved_for_later(id):
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM cart_saved_later WHERE user_id=%s AND medicine_id=%s",
        (session["user"]["id"], id)
    )
    db.commit()
    cursor.close()
    return redirect("/cart")


@app.route("/cart/move_to_wishlist/<int:id>")
def move_to_wishlist(id):
    if "user" not in session:
        return redirect("/login")

    save_medicine_to_wishlist(id)
    return redirect("/cart")


def save_medicine_to_wishlist(id):
    ensure_cart_feature_schema()
    db = get_db()
    user_id = session["user"]["id"]
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO wishlist (user_id, medicine_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
    """, (user_id, id))
    cursor.execute(
        "DELETE FROM cart WHERE user_id=%s AND medicine_id=%s",
        (user_id, id)
    )
    db.commit()
    cursor.close()


@app.route("/wishlist/add/<int:id>")
def add_to_wishlist(id):
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO wishlist (user_id, medicine_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
    """, (session["user"]["id"], id))
    db.commit()
    cursor.close()
    return redirect(request.referrer or "/wishlist")


@app.route("/cart/wishlist_to_cart/<int:id>")
def wishlist_to_cart(id):
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
    db = get_db()
    user_id = session["user"]["id"]
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO cart (user_id, medicine_id, quantity)
        VALUES (%s, %s, 1)
        ON DUPLICATE KEY UPDATE quantity = quantity + 1
    """, (user_id, id))
    cursor.execute(
        "DELETE FROM wishlist WHERE user_id=%s AND medicine_id=%s",
        (user_id, id)
    )
    db.commit()
    cursor.close()
    return redirect("/cart")


@app.route("/wishlist/move_to_cart/<int:id>")
def wishlist_page_to_cart(id):
    if "user" not in session:
        return redirect("/login")

    wishlist_to_cart(id)
    return redirect("/wishlist")


@app.route("/cart/remove_wishlist/<int:id>")
def remove_wishlist(id):
    if "user" not in session:
        return redirect("/login")

    remove_wishlist_item(id)
    return redirect("/cart")


def remove_wishlist_item(id):
    ensure_cart_feature_schema()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM wishlist WHERE user_id=%s AND medicine_id=%s",
        (session["user"]["id"], id)
    )
    db.commit()
    cursor.close()


@app.route("/wishlist/remove/<int:id>")
def remove_from_wishlist_page(id):
    if "user" not in session:
        return redirect("/login")

    remove_wishlist_item(id)
    return redirect("/wishlist")


@app.route("/wishlist/notify/<int:id>")
def toggle_wishlist_notification(id):
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE wishlist
        SET notify_when_available = CASE WHEN notify_when_available = 1 THEN 0 ELSE 1 END
        WHERE user_id=%s AND medicine_id=%s
    """, (session["user"]["id"], id))
    db.commit()
    cursor.close()
    return redirect("/wishlist")


@app.route("/wishlist")
def wishlist_page():
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicines.id,
               medicines.name,
               medicines.price,
               medicines.stock,
               medicines.prescription_required,
               medicines.expiry_date,
               wishlist.notify_when_available,
               wishlist.created_at
        FROM wishlist
        JOIN medicines ON medicines.id = wishlist.medicine_id
        WHERE wishlist.user_id=%s
        ORDER BY wishlist.created_at DESC
    """, (session["user"]["id"],))
    wishlist_items = cursor.fetchall()
    cursor.execute("SELECT COALESCE(SUM(quantity),0) AS count FROM cart WHERE user_id=%s", (session["user"]["id"],))
    cart_count = (cursor.fetchone() or {}).get("count", 0)
    cursor.close()
    return render_template("wishlist.html", wishlist_items=wishlist_items, cart_count=cart_count)


@app.route("/cart/apply_coupon", methods=["POST"])
def apply_coupon():
    if "user" not in session:
        return redirect("/login")

    code = request.form.get("coupon_code", "").strip().upper()
    if code in CART_COUPONS:
        session["cart_coupon"] = code
        flash(f"Coupon {code} applied.")
    else:
        session.pop("cart_coupon", None)
        flash("Invalid coupon code.")
    return redirect("/cart")


@app.route("/cart/remove_coupon")
def remove_coupon():
    session.pop("cart_coupon", None)
    return redirect("/cart")


# ================= CART PAGE =================
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/login")

    ensure_cart_feature_schema()
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
    subtotal_total = 0

    for r in rows:
        subtotal = r["price"] * r["quantity"]
        subtotal_total += subtotal

        items.append({
            "id": r["id"],
            "name": r["name"],
            "price": r["price"],
            "qty": r["quantity"],
            "subtotal": subtotal
        })

    cursor.execute("""
        SELECT medicines.id, medicines.name, medicines.price,
               cart_saved_later.quantity
        FROM cart_saved_later
        JOIN medicines ON medicines.id = cart_saved_later.medicine_id
        WHERE cart_saved_later.user_id=%s
        ORDER BY cart_saved_later.created_at DESC
    """, (user_id,))
    saved_items = cursor.fetchall()

    cursor.execute("""
        SELECT medicines.id, medicines.name, medicines.price
        FROM wishlist
        JOIN medicines ON medicines.id = wishlist.medicine_id
        WHERE wishlist.user_id=%s
        ORDER BY wishlist.created_at DESC
    """, (user_id,))
    wishlist_items = cursor.fetchall()

    cursor.close()
    totals = calculate_cart_totals(subtotal_total)
    return render_template(
        "cart.html",
        items=items,
        saved_items=saved_items,
        wishlist_items=wishlist_items,
        total=totals["payable_total"],
        totals=totals,
        coupons=CART_COUPONS
    )


# ================= CHECKOUT =================
@app.route("/checkout")
def checkout():
    if "user" not in session:
        return redirect("/login")

    ensure_payment_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicines.id,
               medicines.name,
               medicines.price,
               cart.quantity
        FROM cart
        JOIN medicines ON medicines.id = cart.medicine_id
        WHERE cart.user_id=%s
    """, (session["user"]["id"],))
    cart_items = cursor.fetchall()
    cursor.close()

    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    totals = calculate_cart_totals(subtotal)

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        totals=totals,
        payment_methods=PAYMENT_METHODS,
        manual_payment_methods=MANUAL_PAYMENT_METHODS
    )

# ================= PLACE ORDER =================
# ================= PLACE ORDER =================
@app.route("/place_order", methods=["POST"])
def place_order():

    if "user" not in session:
        return redirect("/login")

    ensure_payment_schema()
    db = get_db()

    try:

        # ================= START TRANSACTION =================
        cursor = db.cursor(dictionary=True)
        cursor.execute("BEGIN")

        user_id = session["user"]["id"]
        delivery_address = (request.form.get("address") or "").strip()
        delivery_notes = (request.form.get("delivery_notes") or "").strip()
        delivery_otp = f"{secrets.randbelow(1000000):06d}"
        payment_method = (request.form.get("payment_method") or "").strip()
        transaction_id = (request.form.get("transaction_id") or "").strip()
        payment_notes = (request.form.get("payment_notes") or "").strip()
        payment_screenshot_file = request.files.get("payment_screenshot")
        payment_screenshot_path = None

        if payment_method not in PAYMENT_METHODS:
            db.rollback()
            flash("Please select a valid payment method.")
            return redirect("/checkout")

        if payment_method in ["Debit Card", "Credit Card"]:
            db.rollback()
            flash("Card payments require a payment gateway and are not enabled yet.")
            return redirect("/checkout")

        if payment_method in MANUAL_PAYMENT_METHODS:
            if not transaction_id:
                db.rollback()
                flash("Please enter the UPI transaction ID / UTR number.")
                return redirect("/checkout")
            if not payment_screenshot_file or payment_screenshot_file.filename == "":
                db.rollback()
                flash("Please upload the payment screenshot for manual verification.")
                return redirect("/checkout")

        if payment_screenshot_file and payment_screenshot_file.filename:
            extension = payment_screenshot_file.filename.rsplit(".", 1)[-1].lower()
            if extension not in {"jpg", "jpeg", "png", "webp"}:
                db.rollback()
                flash("Payment screenshot must be JPG, JPEG, PNG, or WEBP.")
                return redirect("/checkout")
            upload_folder = os.path.join("static", "uploads", "payments")
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(
                f"payment_{session['user']['id']}_{secrets.token_hex(8)}.{extension}"
            )
            payment_screenshot_path = os.path.join(upload_folder, filename)
            payment_screenshot_file.save(payment_screenshot_path)

        if not delivery_address:
            cursor.execute("SELECT address FROM users WHERE id=%s", (user_id,))
            user_row = cursor.fetchone() or {}
            delivery_address = user_row.get("address") or "Delivery address not provided"

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
                prescription,
                delivery_status,
                delivery_otp,
                delivery_notes,
                delivery_address,
                delivery_updated_at,
                payment_method,
                payment_status,
                payment_reference,
                payment_screenshot
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            0,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Pending",
            file_path,
            delivery_status_for_order_status("Pending"),
            delivery_otp,
            delivery_notes,
            delivery_address,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            payment_method,
            "Pending Verification" if payment_method in MANUAL_PAYMENT_METHODS else "Pending COD",
            transaction_id or None,
            payment_screenshot_path
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

        totals = calculate_cart_totals(total)
        total = totals["payable_total"]

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

        cursor.execute("""
            INSERT INTO payments (
                order_id,
                user_id,
                method,
                amount,
                transaction_id,
                screenshot,
                status,
                notes,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            order_id,
            user_id,
            payment_method,
            total,
            transaction_id or None,
            payment_screenshot_path,
            "Pending Verification" if payment_method in MANUAL_PAYMENT_METHODS else "Pending COD",
            payment_notes,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        # ================= CLEAR CART =================
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            DELETE FROM cart
            WHERE user_id=%s
        """, (user_id,))
        session.pop("cart_coupon", None)

        # ================= COMMIT =================
        db.commit()
        cursor.close()

        if payment_method in MANUAL_PAYMENT_METHODS:
            flash("Order placed. Payment proof submitted for staff verification.")
        else:
            flash("Order placed successfully.")

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

    ensure_payment_schema()
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
            SELECT medicines.id AS medicine_id, medicines.name, order_items.quantity, order_items.price
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
            "prescription": o.get("prescription"),
            "return_status": o.get("return_status") or "Not Requested",
            "refund_status": o.get("refund_status") or "Not Applicable",
            "tracking_steps": order_tracking_steps(o["status"]),
            "can_cancel": o["status"] in ["Pending", "Approved"],
            "can_return": o["status"] == "Delivered",
            "can_reorder": o["status"] in ["Delivered", "Cancelled", "Refunded"],
            "delivery_status": o.get("delivery_status") or delivery_status_for_order_status(o["status"]),
            "delivery_otp": o.get("delivery_otp") or "Not generated",
            "delivery_notes": o.get("delivery_notes") or "No delivery notes added.",
            "delivery_address": o.get("delivery_address") or "Delivery address not saved.",
            "courier_name": o.get("courier_name") or "Yuvraj Local Delivery",
            "courier_tracking_id": o.get("courier_tracking_id") or f"YMD{o['id']:06d}",
            "courier_tracking_url": o.get("courier_tracking_url") or "",
            "payment_method": o.get("payment_method") or "Cash On Delivery",
            "payment_status": o.get("payment_status") or "Pending",
            "payment_reference": o.get("payment_reference") or "Not provided",
            "payment_screenshot": o.get("payment_screenshot"),
        })


    summary = {
        "total_orders": len(orders),
        "active_orders": len([o for o in orders if o["status"] in ["Pending", "Approved", "Packed", "Out For Delivery"]]),
        "delivered_orders": len([o for o in orders if o["status"] == "Delivered"]),
        "refund_orders": len([o for o in orders if o["refund_status"] != "Not Applicable"]),
    }

    return render_template(
        "my_orders.html",
        orders=orders,
        order_statuses=ORDER_STATUSES,
        summary=summary
    )


def get_customer_order(order_id, user_id):
    ensure_payment_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM orders
        WHERE id=%s AND user_id=%s
    """, (order_id, user_id))
    order = cursor.fetchone()
    cursor.close()
    if not order:
        return None, []

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT medicines.id AS medicine_id, medicines.name, order_items.quantity, order_items.price
        FROM order_items
        JOIN medicines ON medicines.id = order_items.medicine_id
        WHERE order_items.order_id=%s
    """, (order_id,))
    items = cursor.fetchall()
    cursor.close()
    return order, items


@app.route("/payment_history")
def payment_history():
    if "user" not in session:
        return redirect("/login")

    ensure_payment_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT payments.*, orders.status AS order_status
        FROM payments
        JOIN orders ON orders.id = payments.order_id
        WHERE payments.user_id=%s
        ORDER BY payments.id DESC
    """, (session["user"]["id"],))
    payments = cursor.fetchall()
    cursor.close()
    summary = {
        "total": len(payments),
        "verified": len([p for p in payments if p.get("status") == "Verified"]),
        "pending": len([p for p in payments if p.get("status") in ["Pending Verification", "Pending COD"]]),
        "amount": sum(float(p.get("amount") or 0) for p in payments),
    }
    return render_template("payment_history.html", payments=payments, summary=summary)


@app.route("/notifications")
def notifications_page():
    if "user" not in session:
        return redirect("/login")

    notifications, unread_count = get_user_notifications(session["user"]["id"])
    summary = {
        "total": len(notifications),
        "unread": unread_count,
        "types": NOTIFICATION_TYPES,
    }
    return render_template("notifications.html", notifications=notifications, summary=summary)


@app.route("/notifications/mark_read/<int:notification_id>", methods=["POST"])
def mark_notification_read(notification_id):
    if "user" not in session:
        return redirect("/login")

    ensure_notification_schema()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE notifications
        SET is_read=1
        WHERE id=%s AND user_id=%s
    """, (notification_id, session["user"]["id"]))
    db.commit()
    cursor.close()
    return redirect("/notifications")


@app.route("/notifications/mark_all_read", methods=["POST"])
def mark_all_notifications_read():
    if "user" not in session:
        return redirect("/login")

    ensure_notification_schema()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE notifications
        SET is_read=1
        WHERE user_id=%s
    """, (session["user"]["id"],))
    db.commit()
    cursor.close()
    return redirect("/notifications")


@app.route("/reviews_feedback", methods=["GET", "POST"])
def reviews_feedback():
    if "user" not in session:
        return redirect("/login")

    ensure_reviews_feedback_schema()
    db = get_db()
    user_id = session["user"]["id"]

    if request.method == "POST":
        review_type = request.form.get("review_type")
        medicine_id = request.form.get("medicine_id") or None
        order_id = request.form.get("order_id") or None
        rating = request.form.get("rating") or None
        title = (request.form.get("title") or "").strip()
        message = (request.form.get("message") or "").strip()
        issue_category = (request.form.get("issue_category") or "").strip() or None

        if review_type not in REVIEW_TYPES:
            flash("Please select a valid feedback type.")
            return redirect("/reviews_feedback")

        if review_type != "Issue Report":
            try:
                rating = int(rating)
            except (TypeError, ValueError):
                rating = 0
            if rating < 1 or rating > 5:
                flash("Please select a rating from 1 to 5 stars.")
                return redirect("/reviews_feedback")
        else:
            rating = None

        if not message:
            flash("Please write your review or issue details.")
            return redirect("/reviews_feedback")

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO reviews_feedback (
                user_id,
                review_type,
                medicine_id,
                order_id,
                rating,
                title,
                message,
                issue_category,
                status,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Submitted', %s)
        """, (
            user_id,
            review_type,
            medicine_id,
            order_id,
            rating,
            title,
            message,
            issue_category,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()
        cursor.close()
        flash("Thank you. Your review or feedback has been submitted.")
        return redirect("/reviews_feedback")

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT medicines.id, medicines.name
        FROM order_items
        JOIN orders ON orders.id = order_items.order_id
        JOIN medicines ON medicines.id = order_items.medicine_id
        WHERE orders.user_id=%s
        ORDER BY medicines.name ASC
    """, (user_id,))
    purchased_medicines = cursor.fetchall()

    cursor.execute("""
        SELECT id, total, date, status, delivery_status
        FROM orders
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 20
    """, (user_id,))
    orders = cursor.fetchall()

    cursor.execute("""
        SELECT reviews_feedback.*,
               medicines.name AS medicine_name,
               orders.status AS order_status
        FROM reviews_feedback
        LEFT JOIN medicines ON medicines.id = reviews_feedback.medicine_id
        LEFT JOIN orders ON orders.id = reviews_feedback.order_id
        WHERE reviews_feedback.user_id=%s
        ORDER BY reviews_feedback.id DESC
    """, (user_id,))
    feedback_items = cursor.fetchall()
    cursor.close()

    summary = {
        "total": len(feedback_items),
        "medicine": len([item for item in feedback_items if item["review_type"] == "Medicine Rating"]),
        "orders": len([item for item in feedback_items if item["review_type"] == "Order Review"]),
        "delivery": len([item for item in feedback_items if item["review_type"] == "Delivery Experience"]),
        "issues": len([item for item in feedback_items if item["review_type"] == "Issue Report"]),
    }

    return render_template(
        "reviews_feedback.html",
        review_types=REVIEW_TYPES,
        purchased_medicines=purchased_medicines,
        orders=orders,
        feedback_items=feedback_items,
        summary=summary,
    )


@app.route("/order_details/<int:order_id>")
def order_details(order_id):
    if "user" not in session:
        return redirect("/login")

    order, items = get_customer_order(order_id, session["user"]["id"])
    if not order:
        abort(404)

    return render_template(
        "order_details.html",
        order=order,
        items=items,
        tracking_steps=order_tracking_steps(order["status"]),
        can_cancel=order["status"] in ["Pending", "Approved"],
        can_return=order["status"] == "Delivered",
        can_reorder=order["status"] in ["Delivered", "Cancelled", "Refunded"],
    )


@app.route("/order_tracking/<int:order_id>")
def order_tracking(order_id):
    if "user" not in session:
        return redirect("/login")

    order, items = get_customer_order(order_id, session["user"]["id"])
    if not order:
        abort(404)

    return render_template(
        "order_tracking.html",
        order=order,
        items=items,
        tracking_steps=order_tracking_steps(order["status"]),
    )


@app.route("/delivery_tracking/<int:order_id>")
def delivery_tracking(order_id):
    return redirect(f"/order_tracking/{order_id}")


@app.route("/courier_tracking/<int:order_id>")
def courier_tracking(order_id):
    return redirect(f"/order_tracking/{order_id}")


@app.route("/download_invoice/<int:order_id>")
def download_invoice(order_id):
    if "user" not in session:
        return redirect("/login")

    order, items = get_customer_order(order_id, session["user"]["id"])
    if not order:
        abort(404)

    invoice_image = static_image_data_uri("images/order-card-visual-premium.png")
    html = render_template("invoice.html", order=order, items=items, invoice_image=invoice_image)
    response = make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=invoice-{order_id}.html"
    return response


@app.route("/reorder/<int:order_id>")
def reorder(order_id):
    if "user" not in session:
        return redirect("/login")

    order, items = get_customer_order(order_id, session["user"]["id"])
    if not order:
        abort(404)

    db = get_db()
    user_id = session["user"]["id"]
    cursor = db.cursor(dictionary=True)
    added = 0

    for item in items:
        cursor.execute("""
            SELECT stock
            FROM medicines
            WHERE id=%s
        """, (item["medicine_id"],))
        medicine = cursor.fetchone()
        if medicine and medicine["stock"] > 0:
            quantity = min(item["quantity"], medicine["stock"])
            cursor.execute("""
                INSERT INTO cart (user_id, medicine_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
            """, (user_id, item["medicine_id"], quantity))
            added += 1

    db.commit()
    cursor.close()
    flash("Previous order medicines were added to your cart." if added else "No medicines from this order are currently available.")
    return redirect("/cart")


def ensure_subscription_schema():
    if app.config.get("SUBSCRIPTION_SCHEMA_READY"):
        return

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_subscriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            medicine_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            frequency_days INT NOT NULL DEFAULT 30,
            next_refill_date DATE NULL,
            auto_reorder TINYINT(1) NOT NULL DEFAULT 0,
            refill_reminder TINYINT(1) NOT NULL DEFAULT 1,
            repeat_prescription_request_id INT NULL,
            status VARCHAR(40) NOT NULL DEFAULT 'Active',
            notes TEXT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE KEY uniq_user_medicine_subscription (user_id, medicine_id),
            INDEX idx_subscription_user (user_id, status),
            INDEX idx_subscription_refill (next_refill_date)
        )
    """)
    db.commit()
    cursor.close()
    app.config["SUBSCRIPTION_SCHEMA_READY"] = True


def add_medicine_to_customer_cart(user_id, medicine_id, quantity=1):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT stock FROM medicines WHERE id=%s", (medicine_id,))
    medicine = cursor.fetchone()
    if not medicine or medicine["stock"] <= 0:
        cursor.close()
        return False

    quantity = max(1, min(int(quantity or 1), medicine["stock"]))
    cursor.execute("""
        INSERT INTO cart (user_id, medicine_id, quantity)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
    """, (user_id, medicine_id, quantity))
    db.commit()
    cursor.close()
    return True


def build_reorder_subscription_context(user_id):
    ensure_subscription_schema()
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT medicines.id,
               medicines.name,
               medicines.price,
               medicines.stock,
               medicines.prescription_required,
               COUNT(DISTINCT orders.id) AS order_count,
               SUM(order_items.quantity) AS total_quantity,
               MAX(orders.date) AS last_order_date
        FROM order_items
        JOIN orders ON orders.id = order_items.order_id
        JOIN medicines ON medicines.id = order_items.medicine_id
        WHERE orders.user_id=%s
          AND orders.status != 'Cancelled'
        GROUP BY medicines.id, medicines.name, medicines.price, medicines.stock, medicines.prescription_required
        ORDER BY last_order_date DESC, total_quantity DESC
        LIMIT 10
    """, (user_id,))
    buy_again_items = cursor.fetchall()

    cursor.execute("""
        SELECT id, name, price, stock, prescription_required
        FROM medicines
        WHERE stock > 0
        ORDER BY name ASC
        LIMIT 120
    """)
    available_medicines = cursor.fetchall()

    cursor.execute("""
        SELECT medicine_subscriptions.*,
               medicines.name AS medicine_name,
               medicines.price,
               medicines.stock,
               medicines.prescription_required
        FROM medicine_subscriptions
        JOIN medicines ON medicines.id = medicine_subscriptions.medicine_id
        WHERE medicine_subscriptions.user_id=%s
        ORDER BY
            CASE medicine_subscriptions.status WHEN 'Active' THEN 0 ELSE 1 END,
            medicine_subscriptions.next_refill_date ASC,
            medicine_subscriptions.id DESC
    """, (user_id,))
    subscriptions = cursor.fetchall()

    try:
        cursor.execute("""
            SELECT id, status, created_at, matched_medicines
            FROM prescription_requests
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 8
        """, (user_id,))
        prescriptions = cursor.fetchall()
    except mysql.connector.Error:
        prescriptions = []

    cursor.close()

    today = datetime.now().date()
    due_soon = []
    for subscription in subscriptions:
        next_refill = subscription.get("next_refill_date")
        if next_refill and subscription.get("status") == "Active":
            if hasattr(next_refill, "date"):
                next_refill = next_refill.date()
            if next_refill <= today + timedelta(days=7):
                due_soon.append(subscription)

    summary = {
        "buy_again": len(buy_again_items),
        "subscriptions": len([item for item in subscriptions if item.get("status") == "Active"]),
        "auto_reorder": len([item for item in subscriptions if item.get("auto_reorder") and item.get("status") == "Active"]),
        "due_soon": len(due_soon),
        "prescriptions": len(prescriptions),
    }

    return {
        "buy_again_items": buy_again_items,
        "available_medicines": available_medicines,
        "subscriptions": subscriptions,
        "prescriptions": prescriptions,
        "summary": summary,
        "default_next_refill": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
    }


@app.route("/reorder_subscription")
def reorder_subscription():
    if "user" not in session:
        return redirect("/login")

    return render_template(
        "reorder_subscription.html",
        **build_reorder_subscription_context(session["user"]["id"])
    )


@app.route("/buy_again/<int:medicine_id>")
def buy_again(medicine_id):
    if "user" not in session:
        return redirect("/login")

    added = add_medicine_to_customer_cart(session["user"]["id"], medicine_id, 1)
    flash("Medicine added to cart." if added else "This medicine is currently out of stock.")
    return redirect("/cart" if added else "/reorder_subscription")


@app.route("/subscriptions/create", methods=["POST"])
def create_subscription():
    if "user" not in session:
        return redirect("/login")

    ensure_subscription_schema()
    user_id = session["user"]["id"]
    medicine_ids = [medicine_id for medicine_id in request.form.getlist("medicine_ids") if medicine_id]
    if not medicine_ids:
        single_medicine_id = request.form.get("medicine_id")
        medicine_ids = [single_medicine_id] if single_medicine_id else []
    if not medicine_ids:
        flash("Please select at least one medicine to subscribe.")
        return redirect("/reorder_subscription")

    quantity = max(1, int(request.form.get("quantity") or 1))
    frequency_days = int(request.form.get("frequency_days") or 30)
    if frequency_days not in [15, 30, 45, 60, 90]:
        frequency_days = 30
    next_refill_date = request.form.get("next_refill_date") or (datetime.now().date() + timedelta(days=frequency_days)).strftime("%Y-%m-%d")
    auto_reorder = 1 if request.form.get("auto_reorder") == "on" else 0
    refill_reminder = 1 if request.form.get("refill_reminder") == "on" else 0
    repeat_prescription_request_id = request.form.get("prescription_request_id") or None

    db = get_db()
    cursor = db.cursor()
    saved_count = 0
    for medicine_id in medicine_ids:
        cursor.execute("""
            INSERT INTO medicine_subscriptions (
                user_id,
                medicine_id,
                quantity,
                frequency_days,
                next_refill_date,
                auto_reorder,
                refill_reminder,
                repeat_prescription_request_id,
                status,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active', %s, %s)
            ON DUPLICATE KEY UPDATE
                quantity=VALUES(quantity),
                frequency_days=VALUES(frequency_days),
                next_refill_date=VALUES(next_refill_date),
                auto_reorder=VALUES(auto_reorder),
                refill_reminder=VALUES(refill_reminder),
                repeat_prescription_request_id=VALUES(repeat_prescription_request_id),
                status='Active',
                updated_at=VALUES(updated_at)
        """, (
            user_id,
            medicine_id,
            quantity,
            frequency_days,
            next_refill_date,
            auto_reorder,
            refill_reminder,
            repeat_prescription_request_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        saved_count += 1
    db.commit()
    cursor.close()
    flash(f"{saved_count} monthly medicine subscription{'s' if saved_count != 1 else ''} saved.")
    return redirect("/reorder_subscription")


@app.route("/subscriptions/<int:subscription_id>/cart", methods=["POST"])
def subscription_to_cart(subscription_id):
    if "user" not in session:
        return redirect("/login")

    ensure_subscription_schema()
    user_id = session["user"]["id"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT *
        FROM medicine_subscriptions
        WHERE id=%s AND user_id=%s
    """, (subscription_id, user_id))
    subscription = cursor.fetchone()
    cursor.close()
    if not subscription:
        abort(404)

    added = add_medicine_to_customer_cart(user_id, subscription["medicine_id"], subscription["quantity"])
    flash("Subscription medicine added to cart." if added else "Subscription medicine is currently out of stock.")
    return redirect("/cart" if added else "/reorder_subscription")


@app.route("/subscriptions/<int:subscription_id>/status", methods=["POST"])
def update_subscription_status(subscription_id):
    if "user" not in session:
        return redirect("/login")

    action = request.form.get("action")
    if action not in ["Active", "Paused", "Cancelled"]:
        flash("Invalid subscription action.")
        return redirect("/reorder_subscription")

    ensure_subscription_schema()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE medicine_subscriptions
        SET status=%s,
            updated_at=%s
        WHERE id=%s AND user_id=%s
    """, (action, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), subscription_id, session["user"]["id"]))
    db.commit()
    cursor.close()
    flash(f"Subscription marked as {action}.")
    return redirect("/reorder_subscription")


@app.route("/repeat_prescription_order/<int:request_id>")
def repeat_prescription_order(request_id):
    return redirect(f"/add_prescription_to_cart/{request_id}")


@app.route("/return_order/<int:order_id>")
def return_order(order_id):
    if "user" not in session:
        return redirect("/login")

    ensure_payment_schema()
    db = get_db()
    user_id = session["user"]["id"]
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT status, return_status
        FROM orders
        WHERE id=%s AND user_id=%s
    """, (order_id, user_id))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        abort(404)

    if order["status"] != "Delivered":
        cursor.close()
        flash("Only delivered orders can be returned.")
        return redirect("/my_orders")

    cursor.execute("""
        UPDATE orders
        SET return_status='Return Requested',
            refund_status='Processing'
        WHERE id=%s AND user_id=%s
    """, (order_id, user_id))
    db.commit()
    cursor.close()
    flash("Return request submitted. Refund status is now Processing.")
    return redirect(f"/order_details/{order_id}")


@app.route("/verify_payment/<int:payment_id>", methods=["POST"])
def verify_payment(payment_id):
    if "user" not in session or session["user"]["role"] not in ["owner", "staff"]:
        return redirect("/login")

    ensure_payment_schema()
    action = request.form.get("action")
    if action not in ["Verified", "Rejected"]:
        flash("Invalid payment action.")
        return redirect("/staff#orders")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT order_id FROM payments WHERE id=%s", (payment_id,))
    payment = cursor.fetchone()
    if not payment:
        cursor.close()
        flash("Payment record not found.")
        return redirect("/staff#orders")

    cursor.execute("""
        UPDATE payments
        SET status=%s,
            verified_at=%s,
            verified_by=%s
        WHERE id=%s
    """, (
        action,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        session["user"]["id"],
        payment_id
    ))
    cursor.execute("""
        UPDATE orders
        SET payment_status=%s
        WHERE id=%s
    """, (action, payment["order_id"]))
    db.commit()
    cursor.close()
    flash(f"Payment marked as {action}.")
    return redirect("/staff#orders")


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
            "prescription": o.get("prescription")
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


# ================= CANCEL ORDER =================
@app.route("/cancel_order/<int:order_id>")
def cancel_order(order_id):
    if "user" not in session:
        return redirect("/login")

    ensure_order_management_schema()
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

    if order["status"] not in ["Pending", "Approved"]:
        flash("This order cannot be cancelled at the current status.")
        return redirect("/my_orders")


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
        SET status='Cancelled',
            refund_status='Not Applicable',
            return_status='Not Requested'
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

    ensure_delivery_feature_schema()
    db = get_db()

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE orders
        SET status='Delivered',
            delivery_status='Delivered',
            delivery_updated_at=%s
        WHERE id=%s
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))

    db.commit()
    cursor.close()

    return redirect("/staff")


@app.route("/update_order_status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    if "user" not in session or session["user"]["role"] not in ["owner", "staff"]:
        return redirect("/login")

    ensure_delivery_feature_schema()
    status = request.form.get("status")
    if status not in ORDER_STATUSES:
        flash("Invalid order status.")
        return redirect("/staff#orders")

    refund_status = "Not Applicable"
    return_status = "Not Requested"
    if status == "Refunded":
        refund_status = "Completed"
        return_status = "Return Closed"
    elif status == "Cancelled":
        refund_status = "Not Applicable"

    courier_name = (request.form.get("courier_name") or "").strip()
    courier_tracking_id = (request.form.get("courier_tracking_id") or "").strip()
    courier_tracking_url = (request.form.get("courier_tracking_url") or "").strip()
    delivery_notes = (request.form.get("delivery_notes") or "").strip()
    submitted_delivery_otp = (request.form.get("delivery_otp") or "").strip()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT delivery_otp FROM orders WHERE id=%s", (order_id,))
    existing_order = cursor.fetchone() or {}
    if status == "Delivered" and existing_order.get("delivery_otp") and submitted_delivery_otp != existing_order["delivery_otp"]:
        cursor.close()
        flash("Delivery OTP is required to mark this order as Delivered.")
        return redirect("/staff#orders")

    cursor.execute("""
        UPDATE orders
        SET status=%s,
            refund_status=%s,
            return_status=CASE
                WHEN return_status='Return Requested' THEN return_status
                ELSE %s
            END,
            delivery_status=%s,
            courier_name=COALESCE(NULLIF(%s, ''), courier_name),
            courier_tracking_id=COALESCE(NULLIF(%s, ''), courier_tracking_id),
            courier_tracking_url=COALESCE(NULLIF(%s, ''), courier_tracking_url),
            delivery_notes=COALESCE(NULLIF(%s, ''), delivery_notes),
            delivery_updated_at=%s
        WHERE id=%s
    """, (
        status,
        refund_status,
        return_status,
        delivery_status_for_order_status(status),
        courier_name,
        courier_tracking_id,
        courier_tracking_url,
        delivery_notes,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        order_id
    ))
    db.commit()
    cursor.close()
    flash(f"Order #{order_id} updated to {status}.")
    return redirect("/staff#orders")
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

    ensure_payment_schema()
    db = get_db()


    cursor =db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines")
    medicines = cursor.fetchall()
    cursor.close()


    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT orders.*,
               users.name AS customer_name,
               payments.id AS payment_id,
               payments.method AS payment_method,
               payments.transaction_id AS payment_transaction_id,
               payments.screenshot AS payment_screenshot,
               payments.status AS payment_status,
               payments.created_at AS payment_created_at
        FROM orders
        JOIN users ON users.id = orders.user_id
        LEFT JOIN payments ON payments.order_id = orders.id
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
        total_medicines=total_medicines,
        order_statuses=ORDER_STATUSES
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

GENERIC_MEDICINE_WORDS = {
    "tablet", "tablets", "tab", "tabs", "capsule", "capsules", "cap", "caps",
    "syrup", "injection", "injectable", "cream", "ointment", "gel", "drops",
    "drop", "eye", "ear", "nasal", "spray", "inhaler", "solution", "sachet",
    "powder", "patch", "lotion", "suspension", "respules", "iv", "fluid",
    "mg", "ml", "mcg", "gm", "g", "iu", "percent"
}


def normalize_medicine_text(value):
    value = re.sub(r"(\d+)\s*(mg|ml|mcg|gm|g|iu)\b", r"\1 \2", value.lower())
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def meaningful_medicine_tokens(value):
    tokens = normalize_medicine_text(value).split()
    return [
        token
        for token in tokens
        if len(token) > 1 and token not in GENERIC_MEDICINE_WORDS
    ]


def prescription_candidate_lines(text):
    lines = [
        normalize_medicine_text(line)
        for line in text.splitlines()
        if normalize_medicine_text(line)
    ]

    candidates = list(lines)

    for size in (2, 3):
        for index in range(0, max(len(lines) - size + 1, 0)):
            candidates.append(" ".join(lines[index:index + size]))

    if text:
        candidates.append(normalize_medicine_text(text))

    return candidates


# ================= Prescription Medicine Detection =================
def detect_medicines_from_text(text, max_matches=5, min_score=72):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT name FROM medicines")
    medicines = cursor.fetchall()
    cursor.close()

    matches = []
    candidates = prescription_candidate_lines(text)

    for med in medicines:

        if not med["name"]:
            continue

        med_name = normalize_medicine_text(med["name"])
        med_tokens = meaningful_medicine_tokens(med["name"])

        if not med_tokens:
            continue

        best_score = 0

        for candidate in candidates:
            candidate_tokens = meaningful_medicine_tokens(candidate)

            if not candidate_tokens:
                continue

            overlap = set(med_tokens) & set(candidate_tokens)

            if not overlap:
                continue

            if med_tokens[0] not in overlap and len(overlap) < 2:
                continue

            name_score = fuzz.token_sort_ratio(med_name, candidate)
            overlap_score = (len(overlap) / len(set(med_tokens))) * 100
            score = (name_score * 0.7) + (overlap_score * 0.3)

            if score > best_score:
                best_score = score

        if best_score >= min_score:
            matches.append({
                "medicine": med["name"],
                "score": round(best_score, 2)
            })

    matches.sort(key=lambda x: x["score"], reverse=True)

    return matches[:max_matches]
# ================= Upload Prescription =================

@app.route("/upload_prescription", methods=["GET", "POST"])
def upload_prescription():
    if "user" not in session:
        return redirect("/login")

    user_id = session["user"]["id"]

    if request.method == "POST":
        prescription = request.files.get("prescription")

        if not prescription or prescription.filename == "":
            flash("Please upload a prescription file", "error")
            return redirect("/upload_prescription")

        allowed_extensions = {"png", "jpg", "jpeg", "webp", "pdf"}

        filename = secure_filename(prescription.filename)
        ext = filename.rsplit(".", 1)[-1].lower()

        if ext not in allowed_extensions:
            flash("Only PNG, JPG, JPEG, WEBP, and PDF files are allowed", "error")
            return redirect("/upload_prescription")

        os.makedirs(PRESCRIPTION_FOLDER, exist_ok=True)

        new_filename = f"user_{user_id}_{datetime.now().timestamp()}_{filename}"
        save_path = os.path.join(PRESCRIPTION_FOLDER, new_filename)

        prescription.save(save_path)

        if ext == "pdf":
            ocr_text = "PDF uploaded. OCR is available for image prescriptions only. Manual staff review required."
        else:
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


@app.route("/download_prescription/<int:request_id>")
def download_prescription(request_id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if session["user"].get("role") in ["staff", "owner"]:
        cursor.execute("""
            SELECT prescription_image
            FROM prescription_requests
            WHERE id=%s
        """, (request_id,))
    else:
        cursor.execute("""
            SELECT prescription_image
            FROM prescription_requests
            WHERE id=%s AND user_id=%s
        """, (request_id, session["user"]["id"]))

    prescription = cursor.fetchone()
    cursor.close()

    if not prescription or not prescription.get("prescription_image"):
        abort(404)

    filename = os.path.basename(prescription["prescription_image"])
    file_path = os.path.join(PRESCRIPTION_FOLDER, filename)

    if not os.path.exists(file_path):
        abort(404)

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "file"
    return send_from_directory(
        PRESCRIPTION_FOLDER,
        filename,
        as_attachment=True,
        download_name=f"prescription_{request_id}.{extension}"
    )


@app.route("/delete_prescription/<int:request_id>", methods=["POST"])
def delete_prescription(request_id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT prescription_image
        FROM prescription_requests
        WHERE id=%s AND user_id=%s
    """, (request_id, session["user"]["id"]))

    prescription = cursor.fetchone()

    if not prescription:
        cursor.close()
        flash("Prescription request not found", "error")
        return redirect("/my_prescriptions")

    cursor.execute("""
        DELETE FROM prescription_requests
        WHERE id=%s AND user_id=%s
    """, (request_id, session["user"]["id"]))
    db.commit()
    cursor.close()

    filename = os.path.basename(prescription["prescription_image"])
    file_path = os.path.join(PRESCRIPTION_FOLDER, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    flash("Prescription deleted successfully", "success")
    return redirect("/my_prescriptions")
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
