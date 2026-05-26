from flask import Flask, render_template, request, redirect, session, g
#import pymysql
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
    host="localhost",
    user="root",
    password=os.environ.get("DB_PASSWORD"),
    database="medical_store"
)



def get_db():

    if "db" not in g:

        g.db = db_pool.get_connection()

    return g.db
# ================= LOCAL IMAGE SAVE =================

def save_image(file):

    upload_folder = os.path.join("static", "images")

    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)

    filepath = os.path.join(upload_folder, filename)

    file.save(filepath)

    return "/" + filepath.replace("\\", "/")

# ================= HOME (SEARCH + FILTER) =================
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    # 🔥 ROLE BASED REDIRECT
    if session["user"]["role"] == "owner":
        return redirect("/owner_dashboard")

    elif session["user"]["role"] == "staff":
        return redirect("/staff")

    # CUSTOMER CONTINUES NORMAL HOME
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
    cart_rows=cursor.fetchall()
    cursor.close()

    cart = {str(r["medicine_id"]): r["quantity"] for r in cart_rows}
    cart_count = sum(cart.values())

    return render_template(
        "index.html",
        medicines=medicines,
        cart=cart,
        cart_count=cart_count,
        search=search,
        sort=sort,
        category=category
    )

# ================= LOGIN =================
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        db = get_db()

        cursor = db.cursor(dictionary=True)

        cursor.execute(
               "SELECT * FROM users WHERE email=%s",
               (email,)
        )

        user = cursor.fetchone()

        if user:

            pass_login = False

            # ================= HASHED PASSWORD =================
            if user["hashed_password"]:

                if check_password_hash(
                    str(user["hashed_password"]),
                    str(password)
                ):
                    pass_login = True

            # ================= OLD PASSWORD =================
            elif user["password"] == password:

                pass_login = True

                # convert old password to hashed
                new_hash = generate_password_hash(password)

                cursor = db.cursor(dictionary=True)
                cursor.execute(
                    "UPDATE users SET hashed_password=%s WHERE id=%s",
                    (new_hash, user["id"])
                )

                db.commit()
                cursor.close()

            # ================= LOGIN SUCCESS =================
            if pass_login:

                session.clear()

                session.permanent = True

                session["user"] = {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"]
                }

                # role redirect
                if user["role"] == "owner":
                    return redirect("/owner_dashboard")

                elif user["role"] == "staff":
                    return redirect("/staff")

                else:
                    return redirect("/")

        return "❌ Invalid credentials"

    return render_template("login.html")
# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        print(request.form)
        role = request.form.get("role")
        db = get_db()

        try:
            # 🔐 Generate hashed password
            hashed_password = generate_password_hash(request.form["password"])

            # -------- CUSTOMER --------
            if role == "customer":
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    INSERT INTO users (name, email, phone, address, role, hashed_password)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    request.form["name"],
                    request.form["email"],
                    request.form["phone"],
                    request.form["address"],
                    "customer",
                    hashed_password
                ))

            # -------- STAFF --------
            elif role == "staff":
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    INSERT INTO users (name, email, phone, address, role, hashed_password)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    request.form["name"],
                    request.form["email"],
                    request.form["phone"],
                    request.form["address"],
                    "staff",
                    hashed_password
                ))
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    INSERT INTO staff (
                        name, email, contact, age, gender,
                        religion, address, education, aadhar, pan
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    request.form["name"],
                    request.form["email"],
                    request.form["phone"],
                    request.form["age"],
                    request.form["gender"],
                    request.form["religion"],
                    request.form["address"],
                    request.form["education"],
                    request.form["aadhar"],
                    request.form["pan"]
                ))

            # ✅ Commit AFTER all inserts
            db.commit()
            cursor.close()

            # ✅ Redirect AFTER commit
            return redirect("/login")

        except Exception as e:
            db.rollback()
            return f"Error: {e}"

    return render_template("register.html")
# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= PROFILE =================
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    db = get_db()


    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM users WHERE id=%s
    """, (session["user"]["id"],))
    user=cursor.fetchone()
    cursor.close()
    return render_template("profile.html", user=user)

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

    try:

        cursor = db.cursor()

        # check existing cart item
        cursor.execute("""
            SELECT id, quantity
            FROM cart
            WHERE user_id=%s AND medicine_id=%s
        """, (user_id, id))

        existing = cursor.fetchone()

        # if already exists -> increase
        if existing:

            cursor.execute("""
                UPDATE cart
                SET quantity = quantity + 1
                WHERE user_id=%s AND medicine_id=%s
            """, (user_id, id))

        # else insert new
        else:

            cursor.execute("""
                INSERT INTO cart
                (user_id, medicine_id, quantity)
                VALUES (%s, %s, %s)
            """, (user_id, id, 1))

        db.commit()

        cursor.close()

    except Exception as e:

        db.rollback()

        print("ADD TO CART ERROR:", e)

        return f"Cart Error: {e}"

    return redirect(request.referrer or "/")
    
    
@app.route("/increase/<int:id>")
def increase(id):
    db = get_db()
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

    if "user" not in session:
        return redirect("/login")

    db = get_db()

    try:

        name = request.form.get("name")
        category = request.form.get("category")
        price = request.form.get("price")
        stock = request.form.get("stock")
        expiry = request.form.get("expiry")

        image_url = None

        # ================= IMAGE UPLOAD =================

        file = request.files.get("image")

        if file and file.filename != "":

            image_url = save_image(file)

            if not image_url:
                flash("Image upload failed")

        # ================= INSERT =================

        cursor = db.cursor(dictionary=True)
        cursor.execute("""

            INSERT INTO medicines
            (
                name,
                category,
                price,
                stock,
                expiry_date,
                image
            )

            VALUES (%s, %s, %s, %s, %s, %s)

        """, (

            name,
            category,
            price,
            stock,
            expiry,
            image_url

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

            category = str(row.get("category", "")).strip()
            expiry = str(row.get("expiry", "")).strip()

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
                INSERT INTO medicines (name, price, stock, category, expiry_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, price, stock, category, expiry))

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
        data["category"],
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
#==========testing================

# ================= RUN =================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
