import ast
from pathlib import Path
import unittest
from unittest.mock import Mock

from flask import Flask
from services.registration_validation import validate_registration


class RegistrationValidationTests(unittest.TestCase):
    def test_invalid_staff_fields(self):
        for field, values in {
            'gender': ['7475636', 'invalid'],
            'aadhar': ['vjh fexhf5r', '123456789012', '234'],
            'pan': ['34', 'ABCDE12345'],
            'education': ['1234', '<script>'],
            'age': ['-1', '0', '121', '20.5', '1e2'],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertIsNotNone(validate_registration(dict(role='staff', email='a@example.com', **{field: value})))

    def test_valid_and_optional_fields(self):
        for role in ['staff', 'customer']:
            self.assertIsNone(validate_registration(dict(role=role, email='a@example.com')))
        data = dict(role='staff', email='a@example.com', gender='Other', age='20',
                    aadhar='234567890123', pan='abcde1234f', education='B.Sc. (2024)')
        self.assertIsNone(validate_registration(data))
        self.assertEqual(data['pan'], 'ABCDE1234F')

    def test_direct_posts_rejected_before_database_or_otp(self):
        # Load only the route to avoid application startup's external services.
        tree = ast.parse(Path('app.py').read_text())
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'register')
        route.decorator_list = []
        db = Mock(side_effect=AssertionError('Invalid registration reached the database'))
        import flask
        namespace = dict(flask=flask, validate_registration=validate_registration, get_db=db)
        exec(compile(ast.Module(body=[route], type_ignores=[]), 'app.py', 'exec'), namespace)
        app = Flask(__name__, template_folder=str(Path('templates').resolve()))
        app.add_url_rule('/chatbot', endpoint='chatbot', view_func=lambda: '')
        for action in ['send_otp', 'create_account']:
            with app.test_request_context('/register', method='POST', data=dict(
                    role='staff', email='a@example.com', gender='7475636', action=action)):
                self.assertIn('Please select a valid gender.', namespace['register']())
        db.assert_not_called()


if __name__ == '__main__':
    unittest.main()
