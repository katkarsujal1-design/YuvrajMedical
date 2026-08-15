import unittest

from app import app, ensure_prescription_request_schema, get_db


class StaffDashboardSchemaTests(unittest.TestCase):
    def test_prescription_request_schema_creates_missing_table(self):
        with app.app_context():
            ensure_prescription_request_schema()

            with get_db().cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'prescription_requests'")
                self.assertIsNotNone(cursor.fetchone())

    def test_authenticated_staff_dashboard_loads(self):
        with app.test_client() as client:
            with client.session_transaction() as session:
                session["user"] = {"id": 1, "role": "staff"}

            response = client.get("/staff", follow_redirects=False)
            self.assertNotEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
