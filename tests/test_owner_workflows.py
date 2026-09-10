"""Workflow checks use session-local TEMPORARY copies of the actual MySQL schema.
No persistent data is inserted, updated, or deleted. Close the connection to discard fixtures.
"""
import os
import tempfile
import unittest
from datetime import date
from io import BytesIO
from unittest.mock import patch

@unittest.skipUnless(os.getenv('OWNER_LIVE_TESTS')=='1','Requires MySQL temporary-table test opt-in')
class IsolatedWorkflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mysql.connector
        import app as module
        from werkzeug.security import generate_password_hash
        cls.module=module;cls.app=module.app;cls.app.config['TESTING']=True
        cls.db=mysql.connector.connect(host=os.environ['DB_HOST'],user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'],database=os.environ['DB_NAME'])
        cls.patches=[patch.object(module,'get_db',return_value=cls.db)]
        cls.patches += [patch.object(module,name,return_value=None) for name in vars(module) if name.startswith('ensure_') and callable(getattr(module,name))]
        cls.patches += [patch.object(module,name,return_value=True) for name in ('notify_order_status_sms','notify_payment_status_sms','notify_prescription_status_sms','send_customer_sms')]
        for p in cls.patches:p.start()
        cursor=cls.db.cursor();cursor.execute('SHOW TABLES');cls.tables=[r[0] for r in cursor.fetchall()]
        for table in cls.tables:
            # SHOW TABLES is authoritative; identifiers never come from request input.
            cursor.execute('CREATE TEMPORARY TABLE `'+table+'` LIKE `'+table+'`')
        cursor.close();cls.password_hash=generate_password_hash('temporary-test-password')
        cls.uploads=tempfile.TemporaryDirectory();cls.folder_patch=patch.object(module,'PRESCRIPTION_FOLDER',cls.uploads.name);cls.folder_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.db.close();cls.folder_patch.stop();cls.uploads.cleanup()
        for p in reversed(cls.patches):p.stop()

    def setUp(self):
        cursor=self.db.cursor()
        for table in self.tables:cursor.execute('DELETE FROM `'+table+'`')
        self.db.commit();cursor.close();self.client=self.app.test_client()

    def execute(self,sql,params=()):
        c=self.db.cursor(dictionary=True);c.execute(sql,params); result=c.fetchall() if c.with_rows else c.lastrowid;c.close();self.db.commit();return result

    def fixtures(self):
        for ident,role in [(1,'customer'),(2,'owner'),(3,'staff')]:self.execute('INSERT INTO users (id,name,email,phone,address,role,hashed_password) VALUES (%s,%s,%s,%s,%s,%s,%s)',(ident,'Test '+role,role+'@example.invalid','9000000000','Santacruz',role,self.password_hash))
        self.execute("INSERT INTO medicines (id,name,category,price,stock,expiry_date) VALUES (1,'Temporary test medicine','General',50,10,'2028-01-01')")
        self.execute("INSERT INTO delivery_areas (area_name,base_charge,free_delivery_minimum,estimated_time,is_active) VALUES ('Santacruz',40,500,'1 day',1)")

    def login_session(self,role='owner'):
        with self.client.session_transaction() as session:session['user']={'id':{'owner':2,'customer':1,'staff':3}[role],'role':role,'name':'Test '+role}

    def test_empty_dashboard_and_reports(self):
        from services.owner_dashboard import load_dashboard
        from services.owner_reports import build_report
        data=load_dashboard(self.db,{})
        self.assertTrue(all(v in (None,0) for v in data['metrics'].values()))
        self.assertEqual(data['orders'],[])
        self.login_session()
        self.assertEqual(self.client.get('/owner_dashboard').status_code,200)
        for kind in ('sales','orders','inventory','prescriptions','users'):
            self.assertEqual(build_report(self.db,kind,{})['rows'],[])
            for fmt in ('html','csv','xlsx','pdf'):self.assertEqual(self.client.get('/owner/reports/'+kind+'?format='+fmt).status_code,200)

    def test_login_logout_role_redirects_and_pages(self):
        self.fixtures()
        for role,destination in [('customer','/'),('owner','/owner_dashboard'),('staff','/staff')]:
            response=self.client.post('/login',data={'email':role+'@example.invalid','password':'temporary-test-password'})
            self.assertEqual(response.status_code,302);self.assertEqual(response.location,destination)
            paths={'customer':['/','/cart','/wishlist','/checkout','/my_orders','/upload_prescription'],
                   'owner':['/owner_dashboard','/staff/add-medicine','/staff/orders','/staff_prescriptions'],
                   'staff':['/staff','/staff/orders','/staff/inventory']}[role]
            for path in paths:
                with self.subTest(role=role,path=path):self.assertEqual(self.client.get(path).status_code,200)
            self.assertEqual(self.client.get('/logout').status_code,302)
            with self.client.session_transaction() as session:self.assertNotIn('user',session)

    def test_checkout_cancel_and_owner_status(self):
        self.fixtures();self.login_session('customer')
        self.execute('INSERT INTO cart (user_id,medicine_id,quantity) VALUES (1,1,2)')
        response=self.client.post('/place_order',data={'address':'Santacruz','payment_method':'Cash On Delivery'})
        self.assertEqual(response.location,'/my_orders')
        order=self.execute('SELECT id,delivery_charge FROM orders')[0]
        self.assertEqual(self.execute('SELECT stock FROM medicines')[0]['stock'],8)
        self.login_session('owner')
        self.client.post('/update_order_status/'+str(order['id']),data={'status':'Packed'})
        self.assertEqual(self.execute('SELECT delivery_charge FROM orders')[0]['delivery_charge'],order['delivery_charge'])
        self.client.post('/update_order_status/'+str(order['id']),data={'status':'Cancelled'})
        self.assertEqual(self.execute('SELECT stock FROM medicines')[0]['stock'],10)
        self.client.post('/update_order_status/'+str(order['id']),data={'status':'Cancelled'})
        self.assertEqual(self.execute('SELECT stock FROM medicines')[0]['stock'],10)
        self.client.post('/update_order_status/'+str(order['id']),data={'status':'Pending'})
        self.assertEqual(self.execute('SELECT status FROM orders')[0]['status'],'Cancelled')
        self.login_session('customer');self.execute('INSERT INTO cart (user_id,medicine_id,quantity) VALUES (1,1,2)')
        self.client.post('/place_order',data={'address':'Santacruz','payment_method':'Cash On Delivery'})
        latest=self.execute('SELECT MAX(id) AS id FROM orders')[0]['id']
        self.client.get('/cancel_order/'+str(latest));self.client.get('/cancel_order/'+str(latest))
        self.assertEqual(self.execute('SELECT stock FROM medicines')[0]['stock'],10)

    def test_duplicate_failed_and_refunded_receipts(self):
        from services.owner_dashboard import load_dashboard
        from services.owner_reports import build_report
        self.fixtures()
        for ident,status,refund,payment in [(1,'Delivered','Not Applicable','Verified'),(2,'Cancelled','Not Applicable','Verified'),(3,'Delivered','Processing','Verified'),(4,'Pending','Not Applicable','Rejected')]:
            self.execute('INSERT INTO orders (id,user_id,total,date,status,refund_status,payment_status) VALUES (%s,1,100,NOW(),%s,%s,%s)',(ident,status,refund,payment))
            self.execute('INSERT INTO payments (order_id,user_id,method,amount,status,created_at) VALUES (%s,1,%s,100,%s,NOW())',(ident,'Cash On Delivery',payment))
        self.execute("INSERT INTO payments (order_id,user_id,method,amount,status,created_at) VALUES (1,1,'Cash On Delivery',100,'Verified',NOW())")
        self.assertEqual(load_dashboard(self.db,{})['metrics']['revenue'],100)
        self.assertEqual(build_report(self.db,'sales',{})['summary']['Net revenue'],100)

    def test_prescription_upload(self):
        self.fixtures();self.login_session('customer')
        response=self.client.post('/upload_prescription',data={'prescription':(BytesIO(b'%PDF-1.4\n%%EOF'),'temporary.pdf')},content_type='multipart/form-data')
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.execute('SELECT status FROM prescription_requests')[0]['status'],'Pending Review')

if __name__=='__main__':unittest.main()
