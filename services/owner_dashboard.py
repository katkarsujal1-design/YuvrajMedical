"""Read-only owner analytics against the audited medical_store MySQL schema."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')
PAGE_SIZE = 25
# Checkout stores one full payment per order; newer attempts supersede older ones.
PAYMENT_JOIN = '''LEFT JOIN payments p ON p.id = (
    SELECT MAX(p2.id) FROM payments p2 WHERE p2.order_id = o.id
)'''
ELIGIBLE = """p.status = 'Verified' AND o.payment_status = 'Verified'
    AND COALESCE(o.status, '') NOT IN ('Cancelled', 'Refunded')
    AND COALESCE(o.refund_status, '') NOT IN ('Processing', 'Completed')"""
RECEIPT_DATE = "CONVERT_TZ(COALESCE(p.verified_at, p.created_at, o.date), '+00:00', '+05:30')"
MONEY = 'CAST(COALESCE(p.amount, 0) AS DECIMAL(14,2))'


def now_ist():
    return datetime.now(IST)


def rows(db, sql, params=()):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()


def one(db, sql, params=()):
    return rows(db, sql, params)[0]


def money(value):
    if value is None:
        return '—'
    return f'₹{Decimal(str(value)):,.2f}'


def display_date(value):
    if not value:
        return '—'
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return '—'
    if isinstance(value, datetime):
        value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        return value.astimezone(IST).strftime('%d %b %Y, %I:%M %p')
    return value.strftime('%d %b %Y')


def page_number(args, key):
    try:
        page = int(args.get(key, 1))
    except (ValueError, TypeError):
        raise ValueError('Page must be a positive whole number.')
    if not 1 <= page <= 100000:
        raise ValueError('Page is outside the supported range.')
    return page


def paginate(db, sql, params, args, key):
    page = page_number(args, key)
    result = rows(db, sql + ' LIMIT %s OFFSET %s', [*params, PAGE_SIZE + 1, (page - 1) * PAGE_SIZE])
    return result[:PAGE_SIZE], {'page': page, 'has_next': len(result) > PAGE_SIZE, 'key': key}


def revenue_data(db, start, end):
    today = now_ist().date()
    year_start = today.replace(month=1, day=1)
    previous_year = year_start.replace(year=year_start.year - 1)
    days = (end - start).days + 1
    previous_start = start - timedelta(days=days)
    minimum = min(previous_year, previous_start)
    maximum = max(today, end) + timedelta(days=1)
    daily = rows(db, f'''SELECT DATE({RECEIPT_DATE}) AS day, SUM({MONEY}) AS revenue
        FROM orders o {PAYMENT_JOIN} WHERE {ELIGIBLE}
        AND {RECEIPT_DATE} >= %s AND {RECEIPT_DATE} < %s
        GROUP BY DATE({RECEIPT_DATE}) ORDER BY day''', (minimum, maximum))
    values = {r['day']: Decimal(str(r['revenue'])) for r in daily}

    def total(a, b):
        return sum((v for d, v in values.items() if a <= d <= b), Decimal('0'))

    def compare(a, b):
        delta = a - b
        return {'current': float(a), 'previous': float(b), 'difference': float(delta),
                'growth_percentage': round(float(delta / b * 100), 1) if b else None,
                'trend': 'increase' if delta > 0 else 'decrease' if delta < 0 else 'neutral'}

    week = today - timedelta(days=today.weekday())
    month = today.replace(day=1)
    prior_month_end = month - timedelta(days=1)
    prior_month = prior_month_end.replace(day=1)
    try:
        prior_year_end = today.replace(year=today.year - 1)
    except ValueError:  # Leap day has no counterpart in the previous year.
        prior_year_end = today.replace(year=today.year - 1, day=28)
    cards = {
        'today': compare(total(today, today), total(today - timedelta(days=1), today - timedelta(days=1))),
        'week': compare(total(week, today), total(week - timedelta(days=7), today - timedelta(days=7))),
        'month': compare(total(month, today), total(prior_month, min(prior_month_end, prior_month + timedelta(days=today.day - 1)))),
        'year': compare(total(year_start, today), total(previous_year, prior_year_end)),
    }
    dates = [start + timedelta(days=i) for i in range(days)]
    return {'cards': cards, 'range': {'start': str(start), 'end': str(end)},
            'selected_period': compare(total(start, end), total(previous_start, start - timedelta(days=1))),
            'charts': {'daily': {'labels': [d.strftime('%d %b %Y') for d in dates],
                                 'values': [float(values.get(d, 0)) for d in dates],
                                 'previous_values': [float(values.get(previous_start + timedelta(days=i), 0)) for i in range(days)]}},
            'definition': 'Latest verified payment per order; cancelled/refunded orders and refunds in progress excluded. Grouped by receipt date (IST).'}


def load_dashboard(db, args):
    today = now_ist().date()
    metrics = one(db, f'''SELECT COUNT(*) AS total_orders,
        COALESCE(SUM(DATE(CONVERT_TZ(o.date, '+00:00', '+05:30')) = %s),0) AS today_orders,
        COALESCE(SUM(o.status = 'Pending'),0) AS pending_orders,
        COALESCE(SUM(o.status = 'Delivered'),0) AS delivered_orders,
        COALESCE(SUM(o.status = 'Cancelled'),0) AS cancelled_orders,
        COALESCE(SUM(o.status = 'Out For Delivery'),0) AS transit_orders,
        COALESCE(SUM(o.refund_status = 'Completed'),0) AS refunded_orders,
        COALESCE(SUM(CASE WHEN {ELIGIBLE} THEN {MONEY} ELSE 0 END),0) AS revenue,
        COALESCE(SUM(CASE WHEN {ELIGIBLE} THEN 1 ELSE 0 END),0) AS paid_orders,
        COALESCE(SUM(CASE WHEN COALESCE(o.status,'') NOT IN ('Cancelled','Refunded')
            AND COALESCE(p.status,o.payment_status,'Pending') IN ('Pending','Pending Verification','Pending COD')
            THEN 1 ELSE 0 END),0) AS pending_payments,
        COALESCE(SUM(o.status='Delivered' AND COALESCE(p.status,o.payment_status,'') != 'Verified'),0) AS unverified_deliveries
        FROM orders o {PAYMENT_JOIN}''', (today,))
    metrics.update(one(db, '''SELECT COUNT(*) AS total_users,
        COALESCE(SUM(role='customer'),0) AS customers,
        COALESCE(SUM(role='staff'),0) AS staff_accounts,
        COALESCE(SUM(is_blocked=1),0) AS blocked_users FROM users'''))
    metrics.update(one(db, '''SELECT COUNT(*) AS medicines,
        COALESCE(SUM(stock > 0),0) AS available_stock,
        COALESCE(SUM(stock > 0 AND stock <= COALESCE(low_stock_threshold,10)),0) AS low_stock,
        COALESCE(SUM(stock <= 0),0) AS out_of_stock,
        COALESCE(SUM(stock IS NULL),0) AS unknown_stock,
        COALESCE(SUM(expiry_date < %s),0) AS expired,
        COALESCE(SUM(expiry_date BETWEEN %s AND %s),0) AS expiring
        FROM medicines''', (today, today, today + timedelta(days=30))))
    metrics.update(one(db, '''SELECT COUNT(*) AS prescriptions,
        COALESCE(SUM(status='Pending Review'),0) AS pending_prescriptions,
        COALESCE(SUM(status='Approved'),0) AS approved_prescriptions,
        COALESCE(SUM(status='Rejected'),0) AS rejected_prescriptions FROM prescription_requests'''))
    metrics.update(one(db, '''SELECT COUNT(*) AS reviews, AVG(rating) AS average_rating,
        COALESCE(SUM(status='Submitted'),0) AS submitted_feedback FROM reviews_feedback'''))
    metrics.update(one(db, "SELECT COUNT(*) AS active_subscriptions FROM medicine_subscriptions WHERE status='Active'"))
    metrics.update(one(db, 'SELECT COUNT(*) AS wishlist_entries FROM wishlist'))
    metrics.update(one(db, 'SELECT COUNT(*) AS staff_profiles FROM staff'))
    status_rows = rows(db, "SELECT COALESCE(status,'Unknown') AS label, COUNT(*) AS value FROM orders GROUP BY status ORDER BY value DESC")
    categories = rows(db, "SELECT COALESCE(NULLIF(category,''),'Uncategorised') AS label, COUNT(*) AS value FROM medicines GROUP BY label ORDER BY value DESC, label LIMIT 10")
    payment_mix = rows(db, f'''SELECT COALESCE(p.method,'Unknown') AS label, SUM({MONEY}) AS value
        FROM orders o {PAYMENT_JOIN} WHERE {ELIGIBLE} GROUP BY p.method ORDER BY value DESC''')
    top_medicines = rows(db, f'''SELECT m.id, m.name, SUM(oi.quantity) AS units,
        SUM(CAST(oi.price AS DECIMAL(14,2))*oi.quantity) AS item_sales
        FROM order_items oi JOIN orders o ON o.id=oi.order_id {PAYMENT_JOIN}
        LEFT JOIN medicines m ON m.id=oi.medicine_id WHERE {ELIGIBLE}
        GROUP BY m.id,m.name ORDER BY units DESC LIMIT 5''')
    search = args.get('order_search', '').strip()[:150]
    status = args.get('order_status', '').strip()[:100]
    where, params = ['1=1'], []
    if search:
        where.append('(CAST(o.id AS CHAR) LIKE %s OR u.name LIKE %s OR EXISTS (SELECT 1 FROM order_items oi JOIN medicines m ON m.id=oi.medicine_id WHERE oi.order_id=o.id AND m.name LIKE %s))')
        params += [f'%{search}%'] * 3
    if status:
        where.append('o.status=%s'); params.append(status)
    orders, order_page = paginate(db, f'''SELECT o.id,o.date,o.total,o.status,o.delivery_status,o.delivery_address,
        o.prescription,o.payment_method,COALESCE(p.status,o.payment_status) AS payment_status,
        u.name AS customer_name,
        (SELECT COALESCE(SUM(quantity),0) FROM order_items WHERE order_id=o.id) AS item_count
        FROM orders o LEFT JOIN users u ON u.id=o.user_id {PAYMENT_JOIN}
        WHERE {' AND '.join(where)} ORDER BY o.id DESC''', params, args, 'order_page')
    inventory_where, inventory_params = ['1=1'], []
    inventory_search = args.get('inventory_search', '').strip()[:150]
    stock_filter = args.get('stock', '')
    if inventory_search:
        inventory_where.append('(name LIKE %s OR category LIKE %s OR barcode LIKE %s OR supplier LIKE %s)')
        inventory_params += [f'%{inventory_search}%'] * 4
    stock_filters = {'low': 'stock > 0 AND stock <= COALESCE(low_stock_threshold,10)', 'out': 'stock <= 0',
                     'available': 'stock > 0', 'unknown': 'stock IS NULL', 'expired': 'expiry_date < %s',
                     'expiring': 'expiry_date BETWEEN %s AND %s'}
    if stock_filter and stock_filter not in stock_filters:
        raise ValueError('Invalid stock filter.')
    if stock_filter:
        inventory_where.append(stock_filters[stock_filter])
        if stock_filter == 'expired': inventory_params.append(today)
        if stock_filter == 'expiring': inventory_params += [today, today + timedelta(days=30)]
    medicines, inventory_page = paginate(db, f'''SELECT id,name,category,stock,price,purchase_price,expiry_date,
        supplier,batch_number,barcode,low_stock_threshold FROM medicines
        WHERE {' AND '.join(inventory_where)} ORDER BY id DESC''', inventory_params, args, 'inventory_page')
    user_search = args.get('user_search','').strip()[:150]
    customers, customer_page = paginate(db, '''SELECT u.id,u.name,u.email,u.phone,u.address,u.is_blocked,
        (SELECT COUNT(*) FROM orders WHERE user_id=u.id) AS order_count
        FROM users u WHERE u.role='customer' AND (u.name LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)
        ORDER BY u.id DESC''', [f'%{user_search}%'] * 3, args, 'customer_page')
    # No FK exists. Never assume staff.id == users.id; email is the existing registration/removal link.
    staff, staff_page = paginate(db, '''SELECT s.id,s.name,s.contact,s.address,s.email,s.age,s.gender,s.education
        FROM staff s ORDER BY s.id DESC''', [], args, 'staff_page')
    missing_staff = rows(db, '''SELECT u.id,u.name,u.email,u.phone FROM users u WHERE u.role='staff'
        AND NOT EXISTS (SELECT 1 FROM staff s WHERE s.email=u.email) ORDER BY u.id DESC LIMIT 25''')
    prescriptions, prescription_page = paginate(db, '''SELECT pr.id,pr.created_at,pr.reviewed_at,pr.prescription_image,
        pr.status,pr.staff_note,pr.created_order_id,u.name AS customer_name
        FROM prescription_requests pr LEFT JOIN users u ON u.id=pr.user_id ORDER BY pr.id DESC''', [], args, 'prescription_page')
    movements = rows(db, '''SELECT sm.id,sm.change_quantity,sm.previous_stock,sm.new_stock,sm.reason,sm.created_at,
        m.name AS medicine_name FROM stock_movements sm LEFT JOIN medicines m ON m.id=sm.medicine_id
        ORDER BY sm.id DESC LIMIT 8''')
    activity = rows(db, '''SELECT kind,record_id,event_at,detail FROM (
        (SELECT 'Order' AS kind,id AS record_id,date AS event_at,COALESCE(status,'Unknown') AS detail FROM orders ORDER BY id DESC LIMIT 6)
        UNION ALL (SELECT 'Prescription',id,created_at,COALESCE(status,'Unknown') FROM prescription_requests ORDER BY id DESC LIMIT 6)
        UNION ALL (SELECT 'Payment',id,COALESCE(verified_at,created_at),status FROM payments ORDER BY id DESC LIMIT 6)
        UNION ALL (SELECT 'Stock',id,created_at,reason FROM stock_movements ORDER BY id DESC LIMIT 6)
        UNION ALL (SELECT 'Review',id,created_at,review_type FROM reviews_feedback ORDER BY id DESC LIMIT 6)
        ) events WHERE event_at IS NOT NULL ORDER BY event_at DESC LIMIT 10''')
    revenue = revenue_data(db, today - timedelta(days=29), today)
    return dict(metrics=metrics, orders=orders, order_page=order_page, medicines=medicines,
        inventory_page=inventory_page, customers=customers, customer_page=customer_page,
        staff=staff, staff_page=staff_page, missing_staff=missing_staff,
        prescriptions=prescriptions, prescription_page=prescription_page, movements=movements,
        activity=activity, categories=categories, payment_mix=payment_mix, top_medicines=top_medicines,
        status_rows=status_rows, revenue=revenue, generated_at=now_ist(), today=today)
